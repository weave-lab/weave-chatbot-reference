---
github:
  repo: waml
  path: README.md
  branch: main
lastmod: "2025-04-03 14:03:02"
owner: acl-dev-team-devx@getweave.com
title: WAML™
titleIcon: fa-solid fa-bars-staggered
weight: 500
---

The WAML™ is the `.weave.yaml` file that lives in the root of all service repos. It defines how a service is deployed.

* `name` -- The "friendly" name of your application. For example 'The Deployer' instead of 'the-deployer', this is used
  to occasionally print out user-friendly information about your project
* `slug` -- The GitHub slug of your repo. For example if your repo url is https://github.com/weave-lab/the-deployer
  your slug would be 'the-deployer', this is used by bart to create GitHub deployments
    * The kubernetes name that is used for all the various kubernetes resources (deployments, services, serviceaccounts,
      ingress, ingressroutes, etc.). To help standardize our naming of various resources a single thing is responsible
      for, we want to move in the direction of consistently naming things the same.
* `owner` -- The acl email address for the squad that owns the repo. ie 'acl-dev-team-devx@getweave.com'. This is *not* the same thing as the GitHub owner. acl-dev team is a designation via GCP, and various perissions for acl-teams can also be found in `deployer-resource-sync`.
* `slack` -- The Slack channel where any automated messages should go for this application (builds, alerts, etc.)
    * Should follow the format: `#{slack-channel}`.
    * This is used by the `Weave-Slack-API` and `The-Deployer`. It is critical you also add these bots to your designated Slack channel.
* `namespace` -- The kubernetes namespace where this service will be deployed. It is important you deploy your services to your team's namespace, especially to facilitate communication between services.
* [`dependencies`](#dependencies) -- Optional: used to list repo slugs your service is dependent on.(See [`dependencies`](#dependencies)  section below on how to leverage this field).
* [`documentation`](#documentation) -- Optional: used to configure documentation for your repository.
* [`options`](#top-level-options) -- Optional: waml-scoped options
* [`feature flags`](#top-level-feature-flags) -- Optional: application level feature-flags.
* [`deploy`](#deploy-section) -- Map of strings (clusters) to deployment definitions (see below for details on the deploy
  definitions). This is where our cluster overriding happens.
* [`defaults`](#defaults) -- List of deployment metadata with glob matching for which deploy environment to apply
  defaulting to
* `externalLinks` -- Optional: Used to supply custom links about your repository that will be displayed in [Switchboard](https://switchboard.weavelab.ninja) and other places
  * `title` -- The title of the link
  * `url` -- The URL of the link

Example:
```yaml
externalLinks:
- title: "phone events ui"
  url: "https://someurl.com"
- title: "github documentation on a third party library"
  url: "https://github.com/thirdpartylib"
```

# Deploy Section

The `deploy` section is where we define the environments the app deploys to. It is a map of deployIDs to deployment
metadata. A deployID is made up of the clusterID and a deployRef.
Example: wsf-dev-0-gke1-west4 is the deployID.
@beta would be an example of a deployRef. deployRefs are optional. 

```yaml
deploy:
  { deployID }:
    ...{deploy metadata}
```

or

```yaml
deploy:
  { clusterID }@{ deployRef }:
    ...{deploy metadata}
```

**For example:**

```yaml
deploy:
  wsf-prod-1-gke1-west3:
    ...{deploy metadata}
```

or

```yaml
deploy:
  wsf-prod-1-gke1-west3@beta:
    ...{deploy metadata}
```

See [deploy metadata](./wamlv2/DEPLOYMENT_META.md) for more detailed information.

# Defaults

The `defaults` section is at the top-level just like `deploy` and determines deployment metadata that should be applied
to a matching deployID pattern.

### Examples

Use this as the global defaults for all deploys:

```yaml
defaults:
  - match: "*"
    ...{deploy metadata}
```

Defaults for all deployrefs to a specific deployID(aka cluster):

```yaml
defaults:
  - match: "wsf-prod-1-gke1-west3*"
    ...{deploy metadata}
```

Defaults for all prod phone clusters:

```yaml
defaults:
  - match: "prod-*"
    ...{deploy metadata}
```

**Note: Default VALUES are applied by our template engine as well, and the defaults themselves can be found in the
templates [here](https://github.com/weave-lab/app-templates/tree/master/v2/apps). To use a different template just
specify which template to use under the `template` key in your waml file. For example, to create a cron job with the
default cron job template, add  `template: cronjob-default` to your waml.**

- [Backend default values](https://github.com/weave-lab/app-templates/blob/master/v2/apps/backend-default/defaults.yaml)
- [Frontend default values](https://github.com/weave-lab/app-templates/blob/master/v2/apps/frontend-default/defaults.yaml)
- [Cronjob default values](https://github.com/weave-lab/app-templates/blob/master/v2/apps/cronjob-default/defaults.yaml)

# Dependencies

* Leveraging this field allows your service to subscribe to the `dependency-pr-generator` service! Here you can list repos you want to watch for updates.
If there is an update to the default branch of a watched repo, and you have it listed here in your dependencies field, a pull request can be automatically created and merged in your repository ensuring that your dependency is always kept up to date. 
* Example:
  * `bart` is dependent on the `waml` and `the-deployer` repos. `bart`'s dependency section of the WAML™ looks like this:
  ``` yaml
  dependencies:
  - repo: waml
  - repo: the-deployer
  ```
* In the above example, *everytime* a merge happens on the default branch of either `the-deployer` or `waml` a PR will be created and merged in `bart`, updating the go.mod file to use the new dependencies. 
* *Important*: The first time your team starts using the `PR-Generator`, you will need to add the app to your notification channel by tagging: `@Weave-Slack-API` in the correct channel. If you want these pull requests to come to another channel besides your designated slack alert channel, you can specify a different channel in the "options" field.
  All together, a WAML™ using the PR service could look like this:
```yaml
schema: "2"
name: platform demo
slug: platform-demo
owner: acl-dev-team-devx@getweave.com
slack: "#squad-devx"
namespace: platform
dependencies:
- repo: waml
- repo: the-deployer
options:
  pr-notifications: "#devx-pr-reviews"
```

# Documentation

The `documentation` section is a top-level section that is used to configure the documentation for your service.
Use `bart docs setup` to configure your repo to publish to the docs site.

When a repo is configured, a list of categories will be displayed:
```sh
> bart docs setup

Documentation not setup, starting setup process...
Use the arrow keys to navigate: ↓ ↑ → ←
? What type of repo is this:
  ▸ Service
    Library
    System
    Weave
    CLI
```

By default, `bart docs` will auto-discover the `.md` documents in your repo and publish them.

### Customize files to publish

For custom-control of the files published, run `bart docs setup` and choose `Y` for the `disable automatic paths` option.
```sh
? Do you want to disable automatic paths and discover and write known documentation paths for customization? [y/N]
```

This will discover existing `.md` files and write these paths in `.weave.yaml`:
```yaml
documentation:
  type: Service
  paths:
  - files:
    - README.md
    - DEVELOPMENT.md
    - INSTALL.md
```

Documentation paths can be designated using `files`, `fileGlob`, or `dir`.

```yaml
documentation:
  type: Service
  paths:
  - files:
    - README.md
    - DEVELOPMENT.md
    - INSTALL.md
  - fileGlob: "*.txt"
  - dir: "docs"
  - dir: "pkg"
```

### Renaming docs

Sometimes you want to control the documentation path.
For example - omitting the `pkg` directory: 

```yaml
documentation:
  type: Service
  paths:
  - dir: "pkg/docs"
    rename: "docs"
```
This will publish the docs in the `docs` directory,
instead of `pkg/docs`.

### Using Plugins

The docs system supports plugins as a way to generate docs automatically.

The actual plugins supported can vary over time. But for a good list see the [docs-generator plugins page](https://github.com/weave-lab/docs-generator/blob/main/pkg/plugin/README.md)

# Top-level Options 
Usage:

```yaml
options:
  pr-notifications: "squad-devx-alerts"
```

### Supported Options
- `pr-notifications` -- the Slack channel to send pull requests to (if different from the top-level `slack` field)
- `canary-alert-priority` -- this is the priority of the alert for the canary deployment. Default is `P1`.
-  `finops-*` -- Every service gets certain labels added by default. If you need to update or override these with a different value, you can add that label here. See `the-deployer` [here](https://github.com/weave-lab/the-deployer/blob/ce227af70b71087d2a91bfc4c4767199a2a8c958/pkg/versioned/v2/template/generator/functions.go#L860) for more information.

Example:
```yaml
options:
  finops-name: "some custom name here"
```

# Top-level Feature Flags

Usage:

```yaml
featureFlags:
    dos-something-awesome: true
```
### Supported Feature flags
- Test Alerts:
  If you are deploying a branch to dev-0 and have this feature flag set to true, we will append -testing to the OpsGenie team that is used for alerts allowing you to silence, or re-route these alerts to a different channel that is used for testing purposes.
  First step, create a new team in OpsGenie with the name of {normal-team-name}-testing. You can set up your routing rules to route alerts to "No One". And if you want these "test" alerts to go to a Slack channel, just simply add a Slack integration to the new team for a specific channel.

```yaml
featureFlags:
    enable-testing-alert-team: true
```

- Deploy Form:
  A deploy form can be useful to give more context around what is being deployed. This can be helpful to notify other engineers or possibly even support that a deploy is going out. These events will be available in the slack-subscription-app in any channel.

  You can add a deploy form to ANY PR by simply adding a comment to your PR with the following format:

```markdown
## Deploy Form 
some information here about what is being deployed.
This form respects some basic markdown and newlines.
```

However, if you wish to *require* the deploy form to be present in order to pass current radioactiveman-checks, you can set the following waml feature flag:

```yaml
featureFlags:
    require-deploy-form: true
```


# Typescript Support

All Go structs located inside the wamlv2 package have their Typescript equivalent auto-generated and published [here](https://console.cloud.google.com/artifacts/npm/weave-artifacts/us-central1/weave-npm/@weave%2Fwaml?project=weave-artifacts).

These are generated using [tygo](https://github.com/gzuidhof/tygo) in coordination with the [tygo.yaml](./tygo.yaml) file.

These types are imported for use inside the Switchboard so that the WAML can have type safety without needing to be located
inside the schema repository.
