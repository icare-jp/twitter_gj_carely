# Twitter GJ Carely

[稼働しているTwitterアカウント（iCARE公式アカウント）](https://twitter.com/GJ_Carely)

# これはなに？

感謝を伝えたい人と一緒にTwitter上でメンションすると褒めに来てくれるTwitter Botです。

<img width="599" alt="Twitterでの使用例" src="https://user-images.githubusercontent.com/72296262/174004038-f01974a8-95ca-49be-9eba-03596ea5e544.png">

# 　使い方

## 1. ただユーザーとして使いたい場合

iCAREの公式アカウントである[@GJ_Carely](https://twitter.com/GJ_Carely)を使用することができます。  
感謝を伝えたい人と@GJ_Carelyを同時にメンションしてtweetしてみてください。  
およそ10秒後にTwitter GJ Carelyが褒めに来てくれるはずです。  

## 2. @GJ_CarelyではないTwitter Botを自分で運用したい場合

ポイント制度を導入したいかそうでないかでパターンが分かれます。

## 2-1. ポイント制度は導入しなくてもよい場合（まだ動作確認ができておらず、おそらくエラーが発生してしまうと思います。）

- このリポジトリをcloneします。  
- Bot用のTwitterアカウントを作成し、Developerアカウント登録を行います。  
- Developer PortalからElevatedプランへアップグレードを行います。（メールでのやりとりによる審査があります。）  
- 発行されたAPI Key、API Key Secret、Bearer Token、Access Token、Access Token Secretを環境変数に設定し、twitter_gj_carely.pyで読み込めるようにします。
- twitter_gj_carely.pyを実行してストリームを接続します。（iCAREではAWS EC2インスタンス上で起動しています。）
- もしプログラムが落ちたときに再起動させたい場合は、twitter_gj_carely.serviceをsystemdに読み込ませてください。

## 2-2. ポイント制度を導入したい場合

- 2-1に加えて、DBの接続設定をする必要があります。
- PostgreSQLで以下のテーブルを作成してください。

### usersテーブル

| カラム名      | データ型 |
| ------------- | -------- |
| slack_team_id | string   |
| slack_user_id | string   |
| created_at    | datetime |
| updated_at    | datetime |

### giver_countsテーブル

| カラム名           | データ型 | 
| ------------------ | -------- | 
| user_id            | integer  | 
| appreciation_date  | date     | 
| appreciation_count | integer  | 
| created_at         | datetime | 
| updated_at         | datetime | 

### receiver_countsテーブル

| カラム名           | データ型 | 
| ------------------ | -------- | 
| user_id            | integer  | 
| appreciation_date  | date     | 
| appreciation_count | integer  | 
| created_at         | datetime | 
| updated_at         | datetime | 

# ライセンス

このサービスは[MITライセンス](https://github.com/icare-jp/twitter_gj_carely/blob/main/LICENSE)で公開しています。  
Copyright (c) 2022 iCARE Co., Ltd.  

# 関連記事
- [GJ CarelyがTwitterの世界へ！](https://dev.icare.jpn.com/dev_cat/twitter_gj_carely/)
- [iCARE初のOSS公開までに立ちはだかった壁](https://dev.icare.jpn.com/dev_cat/icare_oss)
