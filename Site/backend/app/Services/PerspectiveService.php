<?php

namespace App\Services;

class PerspectiveService
{
    private static ?array $definition = null;

    // Single source of truth shared with python_service/prism/perspective.py.
    public static function definition(): array
    {
        // Unit tests run without a booted app, so fall back to the repo layout.
        $path = app()->bound('config') ? config('prism.shared_path') : dirname(__DIR__, 3).'/shared';
        return self::$definition ??= json_decode(file_get_contents($path.'/perspective.json'), true, flags: JSON_THROW_ON_ERROR);
    }

    public static function dimensions(?string $question = null): array
    {
        $definition = self::definition();
        return array_map(fn ($dimension) => [...$dimension, 'question' => str_replace('{question}', $question ?? $definition['default_question'], $dimension['question'])], $definition['dimensions']);
    }

    public function assess(string $title): array
    {
        // Headline tone is not the author's political position. Never infer direction
        // from a publisher, party name, generic sentiment, or a quoted accusation.
        $definition = self::definition(); $rules = $definition['headline_rules'];
        $result = [];
        foreach ($definition['dimensions'] as $dimension) {
            $result[$dimension['key']] = ['score' => null, 'confidence' => 0, 'evidence' => '', 'actor' => '', 'reason' => $definition['unscored']['reason'], 'method' => $definition['method']];
        }
        foreach ($rules['dimensions'] as $key => ['positive' => $positive, 'negative' => $negative]) {
            $pos = array_values(array_filter($positive, fn ($word) => str_contains($title, $word)));
            $neg = array_values(array_filter($negative, fn ($word) => str_contains($title, $word)));
            if ((bool) $pos xor (bool) $neg) {
                $result[$key] = ['score' => $pos ? 1 : -1, 'confidence' => $rules['confidence'], 'evidence' => ($pos ?: $neg)[0], 'actor' => $rules['actor'], 'reason' => $rules['reason'], 'method' => $definition['method']];
            }
        }
        return $result;
    }

    public function compare(array $left, array $right, array $dimensions): array
    {
        $rows = []; $opposed = []; $different = false;
        foreach ($dimensions as $dimension) {
            $key = $dimension['key']; $a = $left[$key] ?? []; $b = $right[$key] ?? [];
            $opposition = $dimension['opposition'] ?? false;
            $known = isset($a['score'], $b['score']) && ($a['confidence'] ?? 0) >= 0.6 && ($b['confidence'] ?? 0) >= 0.6;
            $opposite = $known && $a['score'] * $b['score'] < 0 && abs($a['score'] - $b['score']) >= 2;
            $difference = $known ? abs($a['score'] - $b['score']) : null;
            if ($opposite && $opposition) { $opposed[] = $dimension['name']; }
            if ($difference > 0) { $different = true; }
            $rows[] = [...$dimension, 'leftAssessment' => $a, 'rightAssessment' => $b, 'difference' => $difference, 'opposed' => $opposite && $opposition];
        }
        return ['status' => $opposed ? 'opposed' : ($different ? 'different' : 'undetermined'), 'opposed_dimensions' => $opposed, 'dimensions' => $rows];
    }
}
