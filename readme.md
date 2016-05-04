## Installation

First clone the repository

```
git clone --recursive https://github.com/gkovacs/creativity_browsing_survey_analysis
```

Or if you have write access

```
git clone --recursive git@github.com:gkovacs/creativity_browsing_survey_analysis.git
```

Then install dependencies and make a dump of the data from heroku

```
cd creativity_browsing_survey_analysis
pip install -r requirements.txt
npm install -g mongodump_meteor
mongoexport_heroku browsingsurvey
```


