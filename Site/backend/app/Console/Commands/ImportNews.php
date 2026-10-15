<?php

namespace App\Console\Commands;

use App\Services\NewsImporter;
use Illuminate\Console\Command;
use Illuminate\Support\Facades\Cache;

class ImportNews extends Command
{
    protected $signature = 'news:import {--file= : Import an existing JSON snapshot} {--limit=24 : Maximum 1-30 RSS records}';
    protected $description = 'Import a bounded set of UDN RSS metadata, without full article text';
    public function handle(NewsImporter $importer): int
    {
        $limit = filter_var($this->option('limit'), FILTER_VALIDATE_INT);
        if ($limit === false || $limit < 1 || $limit > 30) { $this->error('limit 必須介於 1 到 30'); return self::FAILURE; }
        try {
            if ($file = $this->option('file')) {
                $content = file_get_contents($file);
                $rows = json_decode(ltrim($content, "\xEF\xBB\xBF"), true, flags: JSON_THROW_ON_ERROR);
                if (!is_array($rows) || !array_is_list($rows)) { throw new \RuntimeException('JSON 必須為陣列'); }
                $rows = array_slice($rows, 0, $limit);
            } else {
                if (!Cache::add('udn-import-hour', true, now()->addHour())) { $this->error('RSS 每小時最多擷取一次，請稍後再試。'); return self::FAILURE; }
                $rows = $importer->fetch($limit);
                file_put_contents(storage_path('app/udn-latest.json'), json_encode($rows, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
            }
            $this->info(json_encode($importer->import($rows), JSON_UNESCAPED_UNICODE));
            return self::SUCCESS;
        } catch (\Throwable $exception) { $this->error($exception->getMessage()); return self::FAILURE; }
    }
}
