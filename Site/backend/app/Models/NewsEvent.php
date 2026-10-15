<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;

class NewsEvent extends Model
{
    protected $guarded = [];
    protected function casts(): array { return ['dimensions' => 'array', 'is_demo' => 'boolean']; }
    public function articles(): HasMany { return $this->hasMany(Article::class); }
}
