<?php
// Serve only the Laravel public directory with the project's PHP development server.
$public = realpath(__DIR__.'/backend/public');
$path = rawurldecode(parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH) ?: '/');
$candidate = realpath($public.$path);
if ($path !== '/' && $candidate && str_starts_with($candidate, $public.DIRECTORY_SEPARATOR) && is_file($candidate)) { return false; }
require $public.'/index.php';
