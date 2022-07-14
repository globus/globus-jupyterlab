# Changelog

All notable changes to this project will be documented in this file. See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

## [1.0.0-beta.7](https://github.com/globus/globus-jupyterlab/compare/v1.0.0b6...v1.0.0b7) (2022-07-12)

### Bug Fixes

- Exception from improper handling of non-auth Globus API errors ([25b4ae5](https://github.com/globus/globus-jupyterlab/commit/25b4ae5a12879a3b73352cd2859a34e4bbe0e6da))
- GLOBUS_TRANSFER_SUBMISSION_IS_HUB_SERVICE not properly being picked up ([47cade4](https://github.com/globus/globus-jupyterlab/commit/47cade49751d70558f3cd8e31595eb67ff7940bc))
- Possible exception if notebook is not installed ([31ff718](https://github.com/globus/globus-jupyterlab/commit/31ff718d91a4242b0d3a3a79dc59a3c4be03a49d))

## [1.0.0-beta.6](https://github.com/globus/globus-jupyterlab/compare/v1.0.0b5...v1.0.0b6) (2022-06-24)

### Bug Fixes

* Regression with additional GCS v5.4 required logins generating incorrect login URLs ([5b25909](https://github.com/globus/globus-jupyterlab/commit/5b259095eaabb074bca7bf16d3d7cce35fe57949))

## [1.0.0-beta.5](https://github.com/globus/globus-jupyterlab/compare/v1.0.0b4...v1.0.0b5) (2022-06-23)


### Bug Fixes

* Exception in server extension when submitting normal transfer ([ff14f28](https://github.com/globus/globus-jupyterlab/commit/ff14f28999ae66bec22ab117e801f07517515f8e))
* Globus JupyterLab not recognizing GLOBUS_LOCAL_ENDPOINT ([eccd2ac](https://github.com/globus/globus-jupyterlab/commit/eccd2ace87ef1b42f052de6a65a1888b61d8f06a))
* login when workspaces in url ([f05bd32](https://github.com/globus/globus-jupyterlab/commit/f05bd327ee657c262023260f8c509c53c6986bb3))
* Possible infinite login redirect on HA Collections ([1641565](https://github.com/globus/globus-jupyterlab/commit/16415656745d7a6e54a1dc18b854140f6a6262a9))

## [1.0.0-beta.4](https://github.com/globus/globus-jupyterlab/compare/v1.0.0b3...v1.0.0b4) (2022-06-07)


### Bug Fixes

* Alert dismiss not working ([527daf8](https://github.com/globus/globus-jupyterlab/commit/527daf8b941ea90e1965cf444ffc57a0d41ddf0c))
* login url for hub login ([c462d78](https://github.com/globus/globus-jupyterlab/commit/c462d78277663a0da9e06957e958692eedc2dd99))
* multiple logins, transfer, collection types ([3ddc1c0](https://github.com/globus/globus-jupyterlab/commit/3ddc1c049ca8cc2e915877bd01f3132a19b3bb96))
* prettier pre-commit, error status, and use standard node path for transfer ([2041175](https://github.com/globus/globus-jupyterlab/commit/20411754908e08659296fa28e6a1cdce932bf65f))
* Respond to GCS S3 collection "Credentials Required" errors ([86012f0](https://github.com/globus/globus-jupyterlab/commit/86012f06c036138ed1ff3d70f0b6d6302e8d57b4))
* Transfer Submission not properly responding to auth exceptions ([4af8fe5](https://github.com/globus/globus-jupyterlab/commit/4af8fe5011e74f42ab254a802e658f004c9e3c4f))

## [1.0.0-beta.3](https://github.com/globus/globus-jupyterlab/compare/v1.0.0b2...v1.0.0b3) (2022-05-20)


### Features

* Partial support for using GCS v4 endpoints which need activation ([7722067](https://github.com/globus/globus-jupyterlab/commit/77220677e7a6f169f6df7ae40618f23df01aeb5f))
* Support GCS v5.4 High Assurance Collections ([4f1e766](https://github.com/globus/globus-jupyterlab/commit/4f1e766f1051bdb00b66c8d9f13bb59f7086d2cf))


### Bug Fixes

* Auth improperly reporting logged-in state after tokens expired ([0cb13e2](https://github.com/globus/globus-jupyterlab/commit/0cb13e25cc2b28f18c7a493affacf06d8e245aaa))
* Filter out non-functional endpoints from endpoint searches ([5624c9a](https://github.com/globus/globus-jupyterlab/commit/5624c9a0f7db4af65f1184fe146fc4cbbecce5e3))
* Frontend not prompting for login when required ([7e03910](https://github.com/globus/globus-jupyterlab/commit/7e039100c55b08d1a774843883d4f1d87c72b58c))
* Hide hidden files by default ([28fb701](https://github.com/globus/globus-jupyterlab/commit/28fb7017b768c7d121df46ffde4749d9cd866e1c))
* improper 400 returned by endpoint_search ([ff4d996](https://github.com/globus/globus-jupyterlab/commit/ff4d99666ae9fd9703018a2edcfb1388019930f9))
* Revert minimum required jupyterlab family to 3.1.0 for compatibility ([46433c4](https://github.com/globus/globus-jupyterlab/commit/46433c4481e90b55a3f3a3b10f48a31eabbfda06))

## [1.0.0-beta.2](https://github.com/globus/globus-jupyterlab/compare/v1.0.0b1...v1.0.0b2) (2022-05-02)


### Features

* Make Globus Collection ID/path configurable ([ddba2e7](https://github.com/globus/globus-jupyterlab/commit/ddba2e779f2069331bb0441cbf1669af175b379b))


### Bug Fixes

* `is_hub()` for the config not returning boolean responses ([4c2eaad](https://github.com/globus/globus-jupyterlab/commit/4c2eaad7194fa9becd17bae0ba80326c52397e3b))
* is_gcp() possibly returning true with custom configured collection ([b70189d](https://github.com/globus/globus-jupyterlab/commit/b70189d466582ac090f021fbbe56317cb99eb647))
* server extension hiding manual copy-code step ([b88cf93](https://github.com/globus/globus-jupyterlab/commit/b88cf937bed18ccf006f65773a015d6defa94e8a))

## 1.0.0-beta.1 (2022-04-25)

### ⚠ BREAKING CHANGES

* Prune old globus-jupyterlab app

### Features

* Add basic server extension handler api ([3afb240](https://github.com/globus/globus-jupyterlab/commit/3afb24046a7c61efc1f00fd168159403958e36fc))
* Add better failover support for operations requiring data_access ([84b88ca](https://github.com/globus/globus-jupyterlab/commit/84b88ca78a8be2b035f7e52a83143f376c8c3fcb))
* Add endpoint_autoactivate, minor refactor for wrapping sdk posts ([ca6139e](https://github.com/globus/globus-jupyterlab/commit/ca6139e74a5b00693bf39c540146eca8416e94e1))
* Add Login manager for saving/loading toknes ([3075c08](https://github.com/globus/globus-jupyterlab/commit/3075c0815779b7f814425fc3e51aa35e715b0eab))
* Add logout to revoke user tokens ([036ec95](https://github.com/globus/globus-jupyterlab/commit/036ec951ab59eb7240f3e526d921ee0f8fd2c716))
* Add operation_ls and endpoint_search server-extension endpoints ([a5494c0](https://github.com/globus/globus-jupyterlab/commit/a5494c0d9cfbadaa902c199b39e7813a141eb66b))
* Add submit_transfer api endpoint ([98e4257](https://github.com/globus/globus-jupyterlab/commit/98e42573605d61cded1b76e2e63c1e249526cdb3))
* Add support for using custom resource servers ([06fffd5](https://github.com/globus/globus-jupyterlab/commit/06fffd50f057f8db1a7054af6ce2415c389d0248))
* Allow users to copy auth code when automation is unavailable ([a04ca7f](https://github.com/globus/globus-jupyterlab/commit/a04ca7fc9fd0c374a4ba7a947bb92f28454f7bcc))
* Make Globus Collection ID/path configurable ([ddba2e7](https://github.com/globus/globus-jupyterlab/commit/ddba2e779f2069331bb0441cbf1669af175b379b))
* Support Mapped collections via re-login with data_access scope ([5c7726e](https://github.com/globus/globus-jupyterlab/commit/5c7726e4b63d0cea840788b94d75fb55ad4528ef))


### Bug Fixes

* `is_hub()` for the config not returning boolean responses ([4c2eaad](https://github.com/globus/globus-jupyterlab/commit/4c2eaad7194fa9becd17bae0ba80326c52397e3b))
* Add missing style/index.js ([b8544c8](https://github.com/globus/globus-jupyterlab/commit/b8544c8d5ffbfce6daef882f8c3891f7af708b09))
* Bug when fetching collection id ([2492556](https://github.com/globus/globus-jupyterlab/commit/2492556ba1cbd9fa9ef6d02f85343286a0401959))
* Earlier reference to older transfer document schema ([99331a1](https://github.com/globus/globus-jupyterlab/commit/99331a1d4c9798a88cd3015261ef50da38e3a7dd))
* extension bug if GCP owner info is not available ([5309e08](https://github.com/globus/globus-jupyterlab/commit/5309e088660e8379d3ad97e7d80834c2cbe38349))
* incorrect name in setup.py ([3efed70](https://github.com/globus/globus-jupyterlab/commit/3efed709e4f87e21a5d498f90e870beb0e94dd15))
* is_gcp() possibly returning true with custom configured collection ([b70189d](https://github.com/globus/globus-jupyterlab/commit/b70189d466582ac090f021fbbe56317cb99eb647))
* jupyter labextension develop . --overwrite not working ([a48cb81](https://github.com/globus/globus-jupyterlab/commit/a48cb81ee47a9e692d0521497d8372587119158b))
* Old v3 refs causing errors on startup ([80b1a59](https://github.com/globus/globus-jupyterlab/commit/80b1a590133608c5adfd23f2b4f0c58a3d6b68f9))
* Remove tsconfig.spec.json to fix build ([3c05583](https://github.com/globus/globus-jupyterlab/commit/3c0558368a350ae899794c2d9e11acbb09d75d86))
* server extension hiding manual copy-code step ([b88cf93](https://github.com/globus/globus-jupyterlab/commit/b88cf937bed18ccf006f65773a015d6defa94e8a))
* Transfers not submitting correctly ([09cfe45](https://github.com/globus/globus-jupyterlab/commit/09cfe45e166614bb871590fe94eb71d4749b5296))


* Prune old globus-jupyterlab app ([f3ab5c0](https://github.com/globus/globus-jupyterlab/commit/f3ab5c0e266ce506c64c07f55256627a87b47059))
