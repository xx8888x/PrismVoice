<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <meta name="description" content="從不同主張看同一則新聞事件：比較觀點維度、檢查判定依據、追蹤報導時間軸。">
    <title>稜鏡 Prism — 事件與觀點</title>
    <link rel="icon" type="image/svg+xml" href="/prism.svg">
    @vite(['resources/js/app.js'])
</head>
<body><div id="app"></div></body>
</html>
