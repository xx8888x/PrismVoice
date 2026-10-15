<?php
// One-time provisioning of this project's private local MariaDB instance.
$root = __DIR__;
if (file_exists($root.'/.runtime/provisioned')) { exit("Database already provisioned.\n"); }
$pdo = new PDO('mysql:host=127.0.0.1;port=3307;charset=utf8mb4', 'root', '', [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
$password = bin2hex(random_bytes(24));
$testPassword = bin2hex(random_bytes(24));
$rootPassword = bin2hex(random_bytes(24));
foreach (['mediaweb', 'mediaweb_test'] as $database) { $pdo->exec("CREATE DATABASE IF NOT EXISTS `$database` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"); }
foreach (['mediaweb' => $password, 'mediaweb_test' => $testPassword] as $user => $secret) {
    foreach (['localhost', '127.0.0.1'] as $host) {
        $pdo->exec("CREATE USER IF NOT EXISTS '$user'@'$host' IDENTIFIED BY '$secret'");
        $pdo->exec("ALTER USER '$user'@'$host' IDENTIFIED BY '$secret'");
        $pdo->exec("GRANT ALL PRIVILEGES ON `$user`.* TO '$user'@'$host'");
    }
}
$base = "APP_NAME=Prism\nAPP_ENV=local\nAPP_KEY=base64:".base64_encode(random_bytes(32))."\nAPP_DEBUG=false\nAPP_URL=http://127.0.0.1:8088\nAPP_TIMEZONE=UTC\nAPP_LOCALE=zh_TW\nAPP_FALLBACK_LOCALE=en\nLOG_CHANNEL=stack\nDB_CONNECTION=mysql\nDB_HOST=127.0.0.1\nDB_PORT=3307\nDB_DATABASE=mediaweb\nDB_USERNAME=mediaweb\nDB_PASSWORD=$password\nSESSION_DRIVER=file\nSESSION_DOMAIN=null\nSESSION_SAME_SITE=strict\nCACHE_STORE=file\nQUEUE_CONNECTION=sync\n";
file_put_contents($root.'/backend/.env', $base);
$testing = str_replace(['APP_ENV=local', 'DB_DATABASE=mediaweb', 'DB_USERNAME=mediaweb', "DB_PASSWORD=$password"], ['APP_ENV=testing', 'DB_DATABASE=mediaweb_test', 'DB_USERNAME=mediaweb_test', "DB_PASSWORD=$testPassword"], $base);
file_put_contents($root.'/backend/.env.testing', $testing);
file_put_contents($root.'/.runtime/root-client.cnf', "[client]\nhost=127.0.0.1\nport=3307\nuser=root\npassword=$rootPassword\n");
$pdo->exec("DELETE FROM mysql.global_priv WHERE User='root' AND Host=''");
$pdo->exec('FLUSH PRIVILEGES');
$hosts = $pdo->query("SELECT Host FROM mysql.global_priv WHERE User='root'")->fetchAll(PDO::FETCH_COLUMN);
foreach ($hosts as $host) { $pdo->exec('ALTER USER \'root\'@'.$pdo->quote($host)." IDENTIFIED BY '$rootPassword'"); }
file_put_contents($root.'/.runtime/provisioned', date(DATE_ATOM));
echo "Local application and test databases provisioned. Credentials saved locally, not printed.\n";
