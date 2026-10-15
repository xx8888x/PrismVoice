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
}
