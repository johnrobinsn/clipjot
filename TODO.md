# TODO

## Current Scope
-[X] Try on Phone connecting to prod
-[X] Deploy Prod
-[X] Set up Google Auth for Prod
-[ ] Set up Google Auth for Dev
-[ ] Dev Workflow
-[X] Verify Android Studio workflow after URL change
-[X] Change default to clipjot.net
-[X] lowercase clipjot for conda env and repo
-[X] Combine testing of configured URL with savings revert if test fails.
-[X] Add support for certs
-[X] Deal with a large number of URLs
-[X] Make ClipJot WebUI more mobile friendly

## Android Client Launch List
-[X] Setting to `Add Shared Link without Editing`
-[ ] Google Play?
-[X] Consider embedding the clipjot site into the clipjot app so you don't have to install both and manage two logins

## Chrome extension Launch List
-[X] After saving bookmark panel stays open

## Backend Launch List
-[ ] Do I want the webui to prompt to install when on mobile?

## Ready to Ship
-[ ] Mindful usage
-[X] In Android app change gear to a hamburger and have settings, logout and about...
-[ ] Cursor like API for synchronizing links to some processing client.
-[X] Review for consistency (icons, fonts, styles, other branding... ) Pull together a style guide
-[ ] Versioning and Release Process
-[ ] Stop using wildcard cert on ringzero.ai
-[ ] developer docs and llms.txt
-[ ] Enforce user quotas
-[ ] Display what auth provider is in use when logged in?
-[ ] if I change the url and I get logged out
-[ ] Is it possible for me to get the add link panel when I'm signed out
-[ ] IOS Version?
-[ ] db backup strategy
-[ ] validate streaming api and augmenting metadata.
-[ ] Consider upper bounds on all input form elements.
-[ ] Test self hosting it
-[ ] API Synchronization
-[ ] Analytics Config in WebUI

## Futures
-[ ] Full text search
-[ ] Webhooks?
-[ ] Premium Payment Flow
-[ ] IOS sharing
-[ ] Optional hook for X to add a post if we bookmark it
-[ ] ClipJot.ai?

## Operations
-[ ] Setup production Oauth Client for Google
-[ ] Setup production Oauth Client for Github
-[ ] What are best practices for backing up and operationalizing clipjot backend
-[ ] Dockerization
-[ ] Disaster Recovery and Restore From Backups
-[ ] Backup .env files
