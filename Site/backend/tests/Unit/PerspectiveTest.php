<?php

namespace Tests\Unit;

use App\Services\PerspectiveService;
use PHPUnit\Framework\TestCase;

class PerspectiveTest extends TestCase
{
    public function test_opposition_requires_the_same_direction_dimension_and_sufficient_evidence(): void {
        $service = new PerspectiveService;
        $a = ['position' => ['score' => -2, 'confidence' => .9]];
        $b = ['position' => ['score' => 2, 'confidence' => .9]];
        $this->assertSame('opposed', $service->compare($a, $b, $service::dimensions())['status']);
        $b['position']['confidence'] = .55;
        $this->assertSame('undetermined', $service->compare($a, $b, $service::dimensions())['status']);
        $b['position']['score'] = null;
        $this->assertSame('undetermined', $service->compare($a, $b, $service::dimensions())['status']);
    }
    public function test_tone_difference_is_not_political_opposition(): void {
        $service = new PerspectiveService;
        $a = ['tone' => ['score' => -2, 'confidence' => .9]];
        $b = ['tone' => ['score' => 2, 'confidence' => .9]];
        $this->assertSame('different', $service->compare($a, $b, $service::dimensions())['status']);
    }
    public function test_headline_rules_do_not_invent_a_position_from_a_quote_or_publisher(): void {
        $result = (new PerspectiveService)->assess('某人質疑政策，另一人反駁並支持');
        $this->assertNull($result['position']['score']);
        $this->assertLessThan(.6, $result['tone']['confidence']);
    }
    // python_service/tests/test_prism.py runs the same file: both languages must score identically.
    public function test_shared_cases_match_the_python_pipeline(): void {
        $cases = json_decode(file_get_contents(dirname(__DIR__, 3).'/shared/perspective_cases.json'), true, flags: JSON_THROW_ON_ERROR);
        foreach ($cases as $case) {
            $result = (new PerspectiveService)->assess($case['title']);
            $this->assertSame($case['scores'], array_map(fn ($a) => $a['score'], $result), $case['title']);
            $this->assertSame($case['evidence'], array_map(fn ($a) => $a['evidence'], array_filter($result, fn ($a) => $a['score'] !== null)), $case['title']);
        }
    }
    public function test_dimension_without_opposition_flag_never_counts_as_opposed(): void {
        $dimensions = [['key' => 'legacy', 'name' => '舊維度']];
        $a = ['legacy' => ['score' => -2, 'confidence' => .9]]; $b = ['legacy' => ['score' => 2, 'confidence' => .9]];
        $this->assertSame('different', (new PerspectiveService)->compare($a, $b, $dimensions)['status']);
    }
}
