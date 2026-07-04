# skcet timetable -> google calendar sync

automatically pulls your digiicampus timetable and republishes it as an
.ics file that google calendar subscribes to. runs weekly on its own.
the only manual part: refreshing an auth token once a week, because
digicampus expires it every ~7 days and there's no way around that
without handing this script your actual password.

## one-time setup (today)

1. **create a new github repo** (private is fine, doesn't need to be public)
   and push everything in this folder to it.

2. **enable github pages**: repo Settings -> Pages -> Source -> "Deploy from
   a branch" -> branch `main`, folder `/docs`. save. github will give you a
   url that looks like:
   `https://<your-username>.github.io/<repo-name>/timetable.ics`
   that url is what you'll give to google calendar. keep it handy.

3. **add the two secrets** (repo Settings -> Secrets and variables -> Actions
   -> New repository secret):
   - `DIGIICAMPUS_AUTH_TOKEN` — the value from the `Auth-Token` request header
   - `DIGIICAMPUS_COOKIE` — the full value from the `Cookie` request header
   (same devtools process you already did once: Network tab -> the `lessons`
   xhr request -> Headers -> Request Headers)

4. **trigger the workflow manually once** to confirm it works: repo -> Actions
   tab -> "sync-digiicampus-timetable" -> "Run workflow". check the run logs.
   if it says "fetched N lessons, wrote N events" you're golden. if it errors
   out about a bad token, your secrets are wrong or stale — go grab fresh ones.

5. **subscribe in google calendar**: on desktop, gcal -> "Other calendars" (+)
   -> "From URL" -> paste your github pages `.ics` url -> Add calendar.
   google will poll it roughly every 12-24 hours on its own schedule (you
   can't force it faster, that's a google limitation, not mine).

## the weekly bit (every ~7 days, non-negotiable)

your Auth-Token expires roughly every 7.2 days. when it does, the scheduled
run will fail with an HTTP error and just... not update. no explosion, no
crash, no data loss — it just silently stays on the last good snapshot until
you fix it. to fix it:

1. open digicampus in your browser, open devtools -> Network, reload the
   calendar page, find the `lessons` xhr request again
2. copy the new `Auth-Token` and `Cookie` header values
3. update the two github secrets with the fresh values
4. optionally trigger the workflow manually right after, so you don't wait
   for saturday

the workflow is scheduled for saturday mornings assuming you refresh the
token around then — adjust the cron in `.github/workflows/sync.yml` if your
week looks different.

## if something breaks

check the Actions tab -> latest run -> logs. the script is deliberately loud
about *why* it failed (stale token vs weird response vs missing secrets)
instead of failing silently, because silent failures are how you show up to
a 9am that quietly stopped existing three days ago.
