# Twitter/X Observer Quality Report

- Generated at: 2026-04-12T07:03:25.410203+00:00
- Current observed signals: 0
- Best observed signals: 0
- Preferred browser mode: cdp
- Resolved CDP URL: http://127.0.0.1:9222

## Evaluate

- Current run produced 0 signals, so the current attempt is not yet a stable intelligence flow.
- No successful historical run has been preserved yet.
- No behavior bucket produced signals in the current run.
- No adapter route produced signals in the current run.

## Diagnose

- 10 seed/view pages had article cards but still extracted 0 signals, so DOM parsing remains the primary bottleneck.
- 6 seed/view pages showed only stale cards outside the observation window, so profile timelines alone are not sufficient.
- 5 reply pages returned 0 articles, suggesting the `with_replies` route is often inaccessible or differently structured.
- Search fallback pages checked: 5, with 0 pages producing recent-window signals.
- Sample: Sam Altman tweet_post | articles=15 | note=检测到 article，但当前可见卡片均早于时间窗口。
- Sample: Sam Altman like | articles=19 | note=likes 视图被重定向回主页，当前登录态可能无权访问该账号点赞页。
- Sample: Yann LeCun tweet_post | articles=12 | note=检测到 article，但当前可见卡片均早于时间窗口。
- Runtime note: 已通过 CDP 连接浏览器：http://127.0.0.1:9222

## Iterate

- Keep preserving `best` Twitter artifacts so temporary browser failures do not wipe usable signal history.
- Prioritize `tweet_post` plus `search recent` extraction before `reply` and `like`, because timeline pages already show article cards.
- Continue reducing dependence on strict timestamp/status selectors and prefer multiple fallback selectors per card.
