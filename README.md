# License Manager CLI Charm


## Usage

Follow the steps below to get started.

### Build the charm

Running the following command will produce a `.charm` file,
`license-manager-cli.charm`:
```bash
$ make charm
```

### Linter

The linter can be invoked with:

```bash
$ make lint
```

This requires `flake8` and `flake8-docstrings`. Make sure to have them
available, either in a virtual environment or via a native package.

### Create the license-manager-cli charm config

Create a text file `license-manager-cli.yaml` with this content:

```yaml
license-manager-cli:
  license-manager-backend-url: "http://<url-pointing-to-the-license-manager-backend>"
  oidc-domain: "<domain-collected-from-oidc>"
  oidc-client-id: "<client-id-for-oidc-app>"
```

### Deploy the charm

Using the built charm and the defined config, run the following command to
deploy the charm:

```bash
$ juju deploy ./license-manager-cli.charm \
              --config ./license-manager-cli.yaml \
              --series centos7
$ juju relate license-manager-cli login # or any other node where it should be installed
```

### Release the charm
To make a new release of the License Manager CLI Charm:

1. Update the CHANGELOG file, moving the changes under the Unreleased section to the new version section. Always keep an `Unreleased` section at the top.
2. Create a new commit with the title `Release x.y.z`
3. Create a new annotated Git tag, adding a summary of the changes in the tag message:
```bash
$ git tag --annotate --sign x.y.z
```
4. Push the new tag to GitHub:
```bash
$ git push --tags
```

### Change configuration

To modify the charm configuration after it was deployed, use the `juju config` command. For example:
```bash
juju config license-manager-cli license-manager-backend-url=somenewvalue
```