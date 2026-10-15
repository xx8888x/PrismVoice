<?php

namespace App\Services;

class PerspectiveService
{
    public static function dimensions(string $question = '對事件核心措施的態度'): array
    {
        return [
            ['key' => 'position', 'name' => '主張方向', 'question' => $question, 'left' => '反對／質疑', 'right' => '支持／肯定', 'opposition' => true],
            ['key' => 'focus', 'name' => '討論焦點', 'question' => '文字主要聚焦人物攻防，還是制度與政策？', 'left' => '人物攻防', 'right' => '制度政策', 'opposition' => false],
            ['key' => 'tone', 'name' => '表達方式', 'question' => '文字主要呈現衝突，還是協商與合作？', 'left' => '衝突對抗', 'right' => '協商合作', 'opposition' => false],
        ];
    }

    public function assess(string $title): array
    {
        // Headline tone is not the author's political position. Never infer direction
        // from a publisher, party name, generic sentiment, or a quoted accusation.
        $result = [];
        foreach (self::dimensions() as $dimension) {
            $result[$dimension['key']] = ['score' => null, 'confidence' => 0, 'evidence' => '', 'actor' => '', 'reason' => '僅有標題，尚無足夠依據判定主張方向。', 'method' => 'headline-rules-v1'];
        }
        foreach ([
            'focus' => [['制度', '政策', '檢核表', '機組'], ['反諷', '回敬', '酸', '政績宣傳']],
            'tone' => [['合作', '協商', '共同'], ['轟', '反諷', '質疑', '斥', '政治仇恨']],
        ] as $key => [$positive, $negative]) {
            $pos = array_values(array_filter($positive, fn ($word) => str_contains($title, $word)));
            $neg = array_values(array_filter($negative, fn ($word) => str_contains($title, $word)));
            if ((bool) $pos xor (bool) $neg) {
                $result[$key] = ['score' => $pos ? 1 : -1, 'confidence' => 0.55, 'evidence' => ($pos ?: $neg)[0], 'actor' => '標題呈現', 'reason' => '標題詞彙線索，待人工核對；不代表媒體或作者立場。', 'method' => 'headline-rules-v1'];
            }
        }
        return $result;
    }

    public function compare(array $left, array $right, array $dimensions): array
    {
        $rows = []; $opposed = []; $different = false;
        foreach ($dimensions as $dimension) {
            $key = $dimension['key']; $a = $left[$key] ?? []; $b = $right[$key] ?? [];
            $known = isset($a['score'], $b['score']) && ($a['confidence'] ?? 0) >= 0.6 && ($b['confidence'] ?? 0) >= 0.6;
            $opposite = $known && $a['score'] * $b['score'] < 0 && abs($a['score'] - $b['score']) >= 2;
            $difference = $known ? abs($a['score'] - $b['score']) : null;
            if ($opposite && $dimension['opposition']) { $opposed[] = $dimension['name']; }
            if ($difference > 0) { $different = true; }
            $rows[] = [...$dimension, 'leftAssessment' => $a, 'rightAssessment' => $b, 'difference' => $difference, 'opposed' => $opposite && $dimension['opposition']];
        }
        return ['status' => $opposed ? 'opposed' : ($different ? 'different' : 'undetermined'), 'opposed_dimensions' => $opposed, 'dimensions' => $rows];
    }
}
