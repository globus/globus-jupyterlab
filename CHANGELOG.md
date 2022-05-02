# Changelog

All notable changes to this project will be documented in this file. See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

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
