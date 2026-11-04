<a id="readme-top"></a>

<!-- PROJECT SHIELDS -->
<div align="center">

[![Stargazers][stars-shield]][stars-url]
[![Forks][forks-shield]][forks-url]
[![Issues][issues-shield]][issues-url]

</div>

<!-- PROJECT HEADER -->
<br />
<div align="center">

<h3 align="center">mishcal</h3>

  <p align="center">
    a calendar importer from my college app to google calendar.
    <br />
    because opening a college app every morning to find out where i'm supposed to be is a lifestyle i refuse to live.
    <br />
    <a href="https://github.com/mishtiiikrishnaa/mishcal"><strong>explore the repo »</strong></a>
    <br />
    <br />
    <a href="https://github.com/mishtiiikrishnaa/mishcal/issues/new?labels=bug">report bug</a>
    ·
    <a href="https://github.com/mishtiiikrishnaa/mishcal/issues/new?labels=enhancement">request feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>table of contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">about the project</a>
      <ul>
        <li><a href="#built-with">built with</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">getting started</a>
      <ul>
        <li><a href="#prerequisites">prerequisites</a></li>
        <li><a href="#installation">installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">usage</a></li>
    <li><a href="#project-status">project status</a></li>
    <li><a href="#contributing">contributing</a></li>
    <li><a href="#contact">contact</a></li>
    <li><a href="#acknowledgments">acknowledgments</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## about the project

**mishcal** takes my class timetable out of my college's digiicampus portal and turns it into a calendar feed that google calendar can subscribe to. no more screenshotting the timetable and squinting at it later.

a small python script calls the portal's lessons api (the same one its own calendar page uses), turns the lessons into an `.ics` file, and a github action does it all again on a schedule so the calendar stays fresh.

here's what you get:

* **a rolling window:** from 3 days ago to 56 days (about 8 weeks) ahead, so there's plenty of runway between refreshes
* **proper events:** each lesson is titled with its course name and code, with the faculty, batch and department in the description
* **cancellations that show up:** cancelled lessons are marked `CANCELLED:` instead of silently vanishing
* **no duplicates:** every event has a stable id based on the lesson id, so a changed lesson updates in place
* **the right timezone:** everything is set to `Asia/Kolkata`
* **self-refreshing:** the feed asks calendar apps to re-check it every 12 hours
* **secrets stay secret:** the login token and cookie only ever live in github actions secrets, never in the repo
* **no dependencies:** it's pure python standard library

### how it works

```
digiicampus lessons api → fetch_and_build.py → docs/timetable.ics → google calendar
         ↑                         ↑
   auth token + cookie       runs in github actions
   (github secrets)          (scheduled, or by hand)
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



### built with

* [![Python][python-shield]][python-url]
* [![GitHub Actions][actions-shield]][actions-url]
* the [icalendar format (rfc 5545)](https://datatracker.ietf.org/doc/html/rfc5545), written by hand

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## getting started

heads up: this was built around my own classes at my own college, so you'll need to adapt it to yours.

### prerequisites

* python 3 (nothing to `pip install`)
* a github account, since the action and the secrets live there
* a login for your college's digiicampus portal

### installation

1. fork the repo and clone it
   ```sh
   git clone https://github.com/<your-username>/mishcal.git
   cd mishcal
   ```
2. open `fetch_and_build.py` and change these to match your own college:
   * `CLASS_IDS`: the ids of your classes. mine are hard-coded, so yours will differ.
   * `BASE_URL`: your college's portal address.
3. grab a fresh **Auth-Token** and **Cookie** from your browser:
   * log in to the portal and open your browser's devtools (network tab)
   * open the calendar page and click the request to the `lessons` endpoint
   * copy the `Auth-Token` and `Cookie` values from the request headers
4. add them as secrets in your fork under **settings → secrets and variables → actions**:

   | secret name | value |
   | ----------- | ----- |
   | `DIGIICAMPUS_AUTH_TOKEN` | your `Auth-Token` header |
   | `DIGIICAMPUS_COOKIE` | your `Cookie` header |

5. open the **actions** tab and run the workflow once by hand to generate `docs/timetable.ics`.

**never commit your token or cookie.** they're basically your login. they belong in github secrets and nowhere else.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## usage

### subscribing in google calendar

1. publish the `docs/` folder so the `timetable.ics` file has a public url (github pages works for this).
2. in google calendar, go to **other calendars → + → from url**.
3. paste the url of `timetable.ics` and hit add.

google calendar decides for itself how often it re-reads a subscribed url (often every several hours up to a day, whatever the feed asks for), so changes don't appear instantly.

### the weekly chore

the portal's login token expires, so about once a week:

1. grab a fresh `Auth-Token` and `Cookie` from your browser's devtools, the same way you did the first time.
2. update the two github secrets.
3. wait for the next scheduled run, or trigger it by hand from the **actions** tab.

that's the whole manual step. thirty seconds, once a week.

if a run fails with an http error or "response wasn't valid json", it nearly always means the token has expired. refresh the secrets and run it again. the script stops instead of writing a broken calendar, so your old one stays intact.

### running it locally

```sh
export DIGIICAMPUS_AUTH_TOKEN="your-token"
export DIGIICAMPUS_COOKIE="your-cookie"
python fetch_and_build.py
```

it prints how many lessons it fetched and how many events it wrote, and saves the result to `docs/timetable.ics`.

### project files

```
mishcal/
├── .github/workflows/   # the scheduled github action
├── docs/                # the generated timetable.ics
├── fetch_and_build.py   # fetches lessons and builds the .ics
└── README.md
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- PROJECT STATUS -->
## project status

**working**, with one weekly chore (refreshing the login token). it does the one job it was built for.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTRIBUTING -->
## contributing

since this is wired up to my own classes, the best way to use it is to **fork it** and point it at yours. if you spot a genuine bug, feel free to open an issue.

1. fork the project
2. create your feature branch (`git checkout -b feature/AmazingFeature`)
3. commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. push to your branch (`git push origin feature/AmazingFeature`)

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- ACKNOWLEDGMENTS -->
## acknowledgments

* [best-readme-template](https://github.com/othneildrew/Best-README-Template), the template this readme is built on
* [rfc 5545](https://datatracker.ietf.org/doc/html/rfc5545), the icalendar spec
* [github actions](https://github.com/features/actions)
* [github pages](https://pages.github.com)
* [img shields](https://shields.io)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
[stars-shield]: https://img.shields.io/github/stars/mishtiiikrishnaa/mishcal.svg?style=for-the-badge
[stars-url]: https://github.com/mishtiiikrishnaa/mishcal/stargazers
[forks-shield]: https://img.shields.io/github/forks/mishtiiikrishnaa/mishcal.svg?style=for-the-badge
[forks-url]: https://github.com/mishtiiikrishnaa/mishcal/network/members
[issues-shield]: https://img.shields.io/github/issues/mishtiiikrishnaa/mishcal.svg?style=for-the-badge
[issues-url]: https://github.com/mishtiiikrishnaa/mishcal/issues
[python-shield]: https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=python&logoColor=white
[python-url]: https://www.python.org/
[actions-shield]: https://img.shields.io/badge/github_actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white
[actions-url]: https://github.com/features/actions
