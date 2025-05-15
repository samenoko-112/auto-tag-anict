import os
import argparse
from mutagen.mp4 import MP4, MP4Tags

def clean_path(path):
    """
    パスの正規化と不要な文字の除去
    """
    if path:
        return os.path.normpath(path.strip().strip('"\''))
    return path

def sanitize_filename(filename):
    """
    ファイル名から使用できない文字を安全な文字に置き換え
    """
    # Windowsで使用できない文字を置き換え
    replacements = {
        '/': '／',
        '\\': '＼',
        ':': '：',
        '*': '＊',
        '?': '？',
        '"': '"',
        '<': '＜',
        '>': '＞',
        '|': '｜'
    }
    for old, new in replacements.items():
        filename = filename.replace(old, new)
    return filename

def get_mp4_metadata(file_path):
    """
    MP4ファイルからエピソード番号を取得
    """
    file_path = clean_path(file_path)
    print(f"メタデータ取得中: {file_path}")

    try:
        video = MP4(file_path)

        # track (通常のエピソード番号)
        track_number = video.tags.get("trkn")
        if track_number:
            print(f"取得成功: track -> {track_number}")
            if isinstance(track_number[0], tuple):
                track_number = track_number[0][0]  # 例: (1, 0) の場合、1を取得
            elif isinstance(track_number[0], str):
                track_number = int(''.join(filter(str.isdigit, track_number[0])))  # 文字列なら整数に変換
            if track_number > 0:
                return track_number
        
        # episode_sort (エピソード番号として保存されることがある)
        episode_sort = video.tags.get("----:com.apple.iTunes:episode_sort")
        if episode_sort:
            print(f"取得成功: episode_sort -> {episode_sort}")
            if isinstance(episode_sort[0], str):
                return int(episode_sort[0])  # 文字列なら整数に変換

        print(f"取得失敗: {file_path}")
        return None

    except Exception as e:
        print(f"メタデータ取得エラー: {file_path} -> {e}")
        return None

def set_mp4_metadata(file_path, episode_number, episode_title, anime_title, is_movie=False, season_number=1):
    """
    MP4ファイルのメタデータを設定
    - エピソード情報
    - アニメタイトル
    - シーズン情報
    - 劇場版フラグ
    """
    file_path = clean_path(file_path)
    try:
        video = MP4(file_path)
        if video.tags is None:
            video.tags = MP4Tags()

        video["\xa9nam"] = episode_title  # タイトル
        video["\xa9alb"] = anime_title  # アルバム（アニメ名/シリーズ名）
        
        # TVショー関連のメタデータを追加
        video["tvsh"] = anime_title  # TVショー名
        
        # 劇場版の場合は特別な設定
        if is_movie:
            video["trkn"] = [(1, 1)]  # 映画は1/1として設定
            video["----:com.apple.iTunes:episode_sort"] = [bytes(str(1), "utf-8")]  # ソートも1に
            # ジャンルを映画として設定
            video["\xa9gen"] = "Movie"
            # 映画の場合はTVシーズン・エピソード情報は設定しない
        else:
            # 通常のエピソード
            video["trkn"] = [(episode_number, 0)]  # トラック番号
            video["----:com.apple.iTunes:episode_sort"] = [bytes(str(episode_number), "utf-8")]  # iTunesのエピソードソート
            # TVシーズンとエピソード番号を設定
            video["tvsn"] = [season_number]  # TVシーズン番号
            video["tves"] = [episode_number]  # TVエピソード番号
            # TVシリーズとして設定
            video["\xa9gen"] = "TV Show"

        video.save()
        print(f"メタデータ更新完了: {file_path}")

    except Exception as e:
        print(f"メタデータ設定エラー: {file_path} -> {e}")

def rename_and_update_metadata(directory, anime_title, episode_dict, is_movie=False):
    """
    指定ディレクトリ内のMP4ファイルの
    - ファイル名変更
    - メタデータ更新
    を一括処理
    """
    directory = clean_path(directory)
    # この関数はTVシリーズ（is_movie=False）の場合のみ使用
    for filename in os.listdir(directory):
        if filename.lower().endswith(".mp4"):
            old_path = os.path.join(directory, filename)
            episode_number = get_mp4_metadata(old_path)

            if episode_number and episode_number in episode_dict:
                episode_title = episode_dict[episode_number]
                new_filename = f"{episode_number:02d} - {episode_title}.mp4"
                new_filename = sanitize_filename(new_filename)  # ファイル名をサニタイズ
                new_path = os.path.join(directory, new_filename)

                # メタデータ更新
                set_mp4_metadata(old_path, episode_number, episode_title, anime_title)

                # ファイル名変更
                if not os.path.exists(new_path) or old_path == new_path:  # 重複防止
                    os.rename(old_path, new_path)
                    print(f"リネーム成功: {filename} -> {new_filename}")
                else:
                    print(f"スキップ: {new_filename}（既に存在）")
            else:
                print(f"エピソード番号取得失敗: {filename}")
    
    # 通常のTVシリーズの場合
    else:
        for filename in os.listdir(directory):
            if filename.lower().endswith(".mp4"):
                old_path = os.path.join(directory, filename)
                episode_number = get_mp4_metadata(old_path)

                if episode_number and episode_number in episode_dict:
                    episode_title = episode_dict[episode_number]
                    new_filename = f"{episode_number:02d} - {episode_title}.mp4"
                    new_filename = sanitize_filename(new_filename)  # ファイル名をサニタイズ
                    new_path = os.path.join(directory, new_filename)

                    # メタデータ更新
                    set_mp4_metadata(old_path, episode_number, episode_title, anime_title)

                    # ファイル名変更
                    if not os.path.exists(new_path) or old_path == new_path:  # 重複防止
                        os.rename(old_path, new_path)
                        print(f"リネーム成功: {filename} -> {new_filename}")
                    else:
                        print(f"スキップ: {new_filename}（既に存在）")
                else:
                    print(f"エピソード番号取得失敗: {filename}")

def main():
    """
    メイン処理：
    1. Annictからアニメ情報を取得
    2. エピソード情報の取得
    3. ファイルの一括処理
    """
    from dotenv import load_dotenv
    import requests

    try:
        # コマンドライン引数の設定
        parser = argparse.ArgumentParser(description='Annict APIを使用してアニメのメタデータを更新します')
        parser.add_argument('--token', help='Annict APIのアクセストークン')
        args = parser.parse_args()

        # .envファイルからトークンを読み込み
        load_dotenv()
        ACCESS_TOKEN = os.getenv("ANNICT_TOKEN")

        # コマンドライン引数のトークンがある場合はそちらを優先
        if args.token:
            ACCESS_TOKEN = args.token

        if not ACCESS_TOKEN:
            raise Exception("アクセストークンが設定されていません。.envファイルを作成するか、--tokenオプションで指定してください。")

        title = input("アニメタイトルを入力してください: ")
        
        # Annict API でアニメを検索
        search_url = "https://api.annict.com/v1/works"
        params = {
            "access_token": ACCESS_TOKEN,
            "filter_title": title,
            "sort_season": "asc",
            "per_page": 10
        }
        search_response = requests.get(search_url, params=params)
        search_data = search_response.json()

        if not search_data.get("works"):
            raise Exception(f"Annictに「{title}」の情報が見つかりませんでした。")

        print("検索結果:")
        for i, work in enumerate(search_data["works"], start=1):
            # 劇場版か通常のアニメかを表示
            work_type = "【劇場版】" if "劇場版" in work['title'] or "映画" in work['title'] else ""
            print(f"{i}. {work_type}{work['title']} (ID: {work['id']})")

        selected_index = int(input("表示したいアニメの番号を入力してください: ")) - 1
        if selected_index < 0 or selected_index >= len(search_data["works"]):
            raise Exception("無効な番号が入力されました。")

        selected_anime = search_data["works"][selected_index]
        print(f"\n選択されたアニメ: {selected_anime['title']}\n")
        
        # エピソード情報の有無に基づいて劇場版かどうかを後で判断するための初期化
        is_movie = False

        # Annict API でエピソード情報を取得
        episodes_url = "https://api.annict.com/v1/episodes"
        params = {
            "access_token": ACCESS_TOKEN,
            "filter_work_id": selected_anime["id"],
            "sort_sort_number": "asc",
            "per_page": 50
        }
        episodes_response = requests.get(episodes_url, params=params)
        episodes_data = episodes_response.json()

        episode_dict = {}
        
        if not episodes_data.get("episodes") or len(episodes_data["episodes"]) == 0:
            print("エピソード情報が見つかりませんでした。劇場版として処理します。")
            # エピソードがない場合は自動的に劇場版として処理
            is_movie = True
            episode_dict = {1: selected_anime["title"]}
            print(f"劇場版として「{selected_anime['title']}」を使用します。")
        else:
            print("エピソード一覧:")
            # API から取得したエピソードに順番に番号を割り当てる
            for i, episode in enumerate(episodes_data["episodes"], start=1):
                # API から number が取得できなかった場合は連番（i）を使用
                episode_number = int(episode['number']) if episode['number'] else i
                print(f"{episode_number} : {episode['title']}")
            
            # エピソード情報を辞書にする（numberフィールドがない場合はインデックスを使用）
            episode_dict = {}
            for i, ep in enumerate(episodes_data["episodes"], start=1):
                episode_number = int(ep["number"]) if ep["number"] else i
                episode_dict[episode_number] = ep["title"]
            
            is_movie = False  # エピソード情報がある場合は常に映画フラグをオフに

        # 劇場版とTVシリーズで入力方法を変える
        if is_movie:
            # 劇場版の場合はファイルを直接指定
            target_file = input("処理するMP4ファイルのパスを入力してください: ")
            target_file = clean_path(target_file)
            
            if os.path.exists(target_file) and target_file.lower().endswith(".mp4"):
                # ファイルが存在する場合、ディレクトリとファイル名に分割
                target_directory = os.path.dirname(target_file)
                filename = os.path.basename(target_file)
                
                # 単一ファイル処理
                old_path = target_file
                movie_title = list(episode_dict.values())[0]
                new_filename = f"{movie_title}.mp4"
                new_filename = sanitize_filename(new_filename)  # ファイル名をサニタイズ
                new_path = os.path.join(target_directory, new_filename)
                
                # メタデータ更新
                set_mp4_metadata(old_path, 1, movie_title, selected_anime["title"], is_movie=True)
                
                # ファイル名変更
                if old_path != new_path:
                    if not os.path.exists(new_path):
                        os.rename(old_path, new_path)
                        print(f"リネーム成功: {filename} -> {new_filename}")
                    else:
                        print(f"スキップ: {new_filename}（既に存在）")
                else:
                    print("メタデータのみ更新しました。ファイル名は変更ありません。")
            else:
                print("指定されたMP4ファイルが存在しません。")
        else:
            # TVシリーズの場合はディレクトリを指定
            target_directory = input("MP4ファイルのディレクトリを入力してください: ")
            target_directory = clean_path(target_directory)

            if os.path.exists(target_directory):
                rename_and_update_metadata(target_directory, selected_anime["title"], episode_dict, is_movie)
            else:
                print("指定されたディレクトリが存在しません。")

    except Exception as e:
        print(f"\nエラーが発生しました: {str(e)}")
    
    finally:
        # プログラム終了前に入力待ち
        print("\n処理が完了しました。Enterキーを押して終了してください...")
        input()

if __name__ == "__main__":
    main()