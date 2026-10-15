<?php

use App\Http\Controllers\NewsController;
use Illuminate\Support\Facades\Route;

Route::get('/', fn () => view('app'));
Route::prefix('api')->group(function () {
    Route::get('/events', [NewsController::class, 'index']);
    Route::get('/events/{event}', [NewsController::class, 'show']);
    Route::get('/events/{event}/compare', [NewsController::class, 'compare']);
    Route::patch('/articles/{article}', [NewsController::class, 'update']);
    Route::patch('/articles/{article}/event', [NewsController::class, 'move']);
});
