import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { Button, Icon, Form, Checkbox } from 'patternfly-react';
import _ from 'lodash';
import Store from '../../redux/store';
import helpers from '../../common/helpers';
import DropdownSelect from '../dropdownSelect/dropdownSelect';
import { AddSourceWizardField as FieldGroup } from './addSourceWizardField';
import { apiTypes } from '../../constants';
import { sourcesTypes, credentialsTypes } from '../../redux/constants';
import { reduxActions } from '../../redux/actions';

class AddSourceWizardStepTwo extends React.Component {
  static initializeState(nextProps) {
    if (nextProps.source) {
      const credentials = _.get(nextProps.source, apiTypes.API_SOURCE_CREDENTIALS, []);
      let singlePort;
      let singleHostPortDisplay;
      let sslCertVerify;

      if (nextProps.source.sourceType !== 'network' && _.get(nextProps.source, apiTypes.API_SOURCE_HOSTS, []).length) {
        singlePort = _.get(nextProps.source, apiTypes.API_SOURCE_PORT, '');
        singleHostPortDisplay = _.get(nextProps.source, apiTypes.API_SOURCE_HOSTS, '');

        singlePort = singlePort ? `:${singlePort}` : '';
        singleHostPortDisplay = singleHostPortDisplay
          ? `${nextProps.source[apiTypes.API_SOURCE_HOSTS][0]}${singlePort}`
          : '';
      }

      if (nextProps.source.sourceType === 'vcenter' || nextProps.source.sourceType === 'satellite') {
        sslCertVerify = _.get(nextProps.source, ['options', apiTypes.API_SOURCE_SSL_CERT], true);
      }

      return {
        sourceName: _.get(nextProps.source, apiTypes.API_SOURCE_NAME, ''),
        multiHostDisplay: _.get(nextProps.source, apiTypes.API_SOURCE_HOSTS, []).join(',\n'),
        hosts: _.get(nextProps.source, apiTypes.API_SOURCE_HOSTS, []),
        port: _.get(nextProps.source, apiTypes.API_SOURCE_PORT, ''),
        singleHostPortDisplay: singleHostPortDisplay || '',
        credentials: credentials.map(val => val.id),
        sslCertVerify: sslCertVerify || ''
      };
    }

    return {};
  }

  static invalidateStep() {
    Store.dispatch({
      type: sourcesTypes.INVALID_SOURCE_WIZARD_STEPTWO
    });
  }

  static validateSourceName(value) {
    if (value === '') {
      return 'You must enter a source name';
    }

    return null;
  }

  static validateCredentials(value) {
    if (!value.length) {
      return 'You must add a credential';
    }

    return null;
  }

  static validateHosts(value) {
    let validation = null;

    if (value.length) {
      _.each(value, host => {
        if (
          host !== '' &&
          (!new RegExp(
            '^\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.(\\d{1,3}|\\[\\d{1,3}:\\d{1,3}\\]|\\d{1,3}\\/([2][4-9]|30|31|32))$'
          ).test(host) &&
            !new RegExp(
              '^(([a-z0-9]|[a-z0-9][a-z0-9\\-]*[a-z0-9])\\.)*([a-z0-9]|[a-z0-9][a-z0-9\\-]*[a-z0-9])$',
              'i'
            ).test(host))
        ) {
          validation = 'You must enter a valid IP address or hostname';
          return false;
        }

        return true;
      });
    }

    return validation;
  }

  static validateHost(value) {
    if (
      !new RegExp('^\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}$').test(value) &&
      !new RegExp('^(([a-z0-9]|[a-z0-9][a-z0-9\\-]*[a-z0-9])\\.)*([a-z0-9]|[a-z0-9][a-z0-9\\-]*[a-z0-9])$', 'i').test(
        value
      )
    ) {
      return 'You must enter an IP address or hostname';
    }

    return null;
  }

  static validatePort(value) {
    if (value && value.length && !/^\d{1,4}$/.test(value)) {
      return 'Port must be valid';
    }

    return null;
  }

  constructor(props) {
    super(props);

    this.initialState = {
      sourceName: '',
      sourceNameError: null,
      multiHostDisplay: '',
      hosts: [],
      hostsError: null,
      credentials: [],
      credentialsError: null,
      port: '',
      portError: null,
      singleHostPortDisplay: '',
      sslCertVerify: ''
    };

    this.state = { ...this.initialState };
  }

  componentDidMount() {
    const { getWizardCredentials } = this.props;

    this.setState({ ...AddSourceWizardStepTwo.initializeState(this.props) }, () => {
      getWizardCredentials();
      this.validateStep();
    });
  }

  componentWillReceiveProps(nextProps) {
    const nextSourceType = _.get(nextProps, ['source', apiTypes.API_SOURCE_TYPE]);

    if (nextSourceType !== _.get(this.props, ['source', apiTypes.API_SOURCE_TYPE])) {
      let sslCertVerify = '';

      if (nextSourceType === 'vcenter' || nextSourceType === 'satellite') {
        sslCertVerify = _.get(nextProps.source, ['options', apiTypes.API_SOURCE_SSL_CERT], true);
      }

      this.setState(Object.assign({ ...this.initialState }, { sslCertVerify }), () => {
        AddSourceWizardStepTwo.invalidateStep();
      });
    }
  }

  onChangeSourceName = event => {
    this.setState(
      {
        sourceName: event.target.value,
        sourceNameError: AddSourceWizardStepTwo.validateSourceName(event.target.value)
      },
      () => this.validateStep()
    );
  };

  onChangeCredential = credential => {
    const { credentials } = this.state;
    const { source } = this.props;

    const sourceType = _.get(source, apiTypes.API_SOURCE_TYPE);
    let submitCreds = [];

    if (sourceType === 'vcenter' || sourceType === 'satellite') {
      submitCreds = [credential.value];
    } else {
      submitCreds = [...credentials];
      const credentialIndex = submitCreds.indexOf(credential.value);

      if (credentialIndex < 0) {
        submitCreds.push(credential.value);
      } else {
        submitCreds.splice(credentialIndex, 1);
      }
    }

    this.setState(
      { credentials: submitCreds, credentialsError: AddSourceWizardStepTwo.validateCredentials(submitCreds) },
      () => this.validateStep()
    );
  };

  onClickCredential = () => {
    const { source } = this.props;

    Store.dispatch({
      type: credentialsTypes.CREATE_CREDENTIAL_SHOW,
      credentialType: _.get(source, apiTypes.API_SOURCE_TYPE)
    });
  };

  onChangePort = targetValue => {
    const { source } = this.props;
    let value = targetValue;
    let defaultPort;

    switch (_.get(source, apiTypes.API_SOURCE_TYPE)) {
      case 'network':
        defaultPort = 22;
        break;
      case 'satellite':
      case 'vcenter':
        defaultPort = 443;
        break;
      default:
        defaultPort = '';
        break;
    }

    if (value === '') {
      value = defaultPort;
    }

    this.setState(
      {
        port: value,
        portError: AddSourceWizardStepTwo.validatePort(value)
      },
      () => this.validateStep()
    );
  };

  onChangeSslCertVerify = event => {
    this.setState(
      {
        sslCertVerify: event.target.checked || false
      },
      () => this.validateStep()
    );
  };

  onChangeHost = event => {
    const { value } = event.target;
    let host = [];
    let port;

    if (value !== '') {
      [host, port] = value.split(':');
      host = [host];
    }

    const validateHost = AddSourceWizardStepTwo.validateHost(host);
    this.onChangePort(port || '');

    this.setState(
      {
        singleHostPortDisplay: value,
        hosts: host,
        hostsError: validateHost
      },
      () => this.validateStep()
    );
  };

  onChangeHosts = event => {
    const { value } = event.target;
    let hosts = [];

    if (value !== '') {
      hosts = value.replace(/\\n|\\r|\s/g, '').split(',');
      hosts = hosts.filter(host => host !== '');
    }

    this.setState(
      {
        multiHostDisplay: value,
        hosts,
        hostsError: AddSourceWizardStepTwo.validateHosts(hosts)
      },
      () => this.validateStep()
    );
  };

  validateStep() {
    const {
      sourceName,
      sourceNameError,
      hosts,
      hostsError,
      port,
      portError,
      credentials,
      credentialsError,
      sslCertVerify
    } = this.state;
    const { source } = this.props;

    if (
      sourceName !== '' &&
      !sourceNameError &&
      hosts.length &&
      !hostsError &&
      !portError &&
      credentials.length &&
      !credentialsError
    ) {
      const updatedSource = {};

      _.set(updatedSource, apiTypes.API_SOURCE_NAME, sourceName);
      _.set(updatedSource, apiTypes.API_SOURCE_HOSTS, hosts);
      _.set(updatedSource, apiTypes.API_SOURCE_CREDENTIALS, credentials.map(value => parseInt(value, 10)));

      if (port !== '') {
        _.set(updatedSource, apiTypes.API_SOURCE_PORT, port);
      }

      if (sslCertVerify !== '') {
        _.set(updatedSource, ['options', apiTypes.API_SOURCE_SSL_CERT], sslCertVerify);
      }

      Store.dispatch({
        type: sourcesTypes.UPDATE_SOURCE_WIZARD_STEPTWO,
        source: Object.assign({ ...source }, updatedSource)
      });
    } else {
      AddSourceWizardStepTwo.invalidateStep();
    }
  }

  credentialInfo(id) {
    const { allCredentials } = this.props;

    return _.find(allCredentials, { id }) || {};
  }

  renderHosts() {
    const { hostsError, port, portError, multiHostDisplay, singleHostPortDisplay } = this.state;
    const { source } = this.props;

    const sourceType = _.get(source, apiTypes.API_SOURCE_TYPE);

    switch (sourceType) {
      case 'network':
        return (
          <React.Fragment>
            <FieldGroup label="Search Addresses" error={hostsError} errorMessage={hostsError}>
              <Form.FormControl
                componentClass="textarea"
                name="hosts"
                value={multiHostDisplay}
                rows={5}
                placeholder="Enter values separated by commas"
                onChange={this.onChangeHosts}
              />
              <Form.HelpBlock>
                IP addresses, IP ranges, DNS host names, and wildcards are valid. Use CIDR or Ansible notation for
                ranges.
              </Form.HelpBlock>
            </FieldGroup>
            <FieldGroup label="Port" error={portError} errorMessage={portError}>
              <Form.FormControl
                name="port"
                type="text"
                value={port}
                placeholder="Default port is 22"
                onChange={e => this.onChangePort(e.target.value)}
              />
            </FieldGroup>
          </React.Fragment>
        );

      case 'vcenter':
      case 'satellite':
        return (
          <React.Fragment>
            <FieldGroup
              label="IP Address or Hostname"
              error={hostsError || portError}
              errorMessage={hostsError || portError}
            >
              <Form.FormControl
                name="hosts"
                type="text"
                value={singleHostPortDisplay}
                placeholder="Enter an IP address or hostname (default port is 443)"
                onChange={this.onChangeHost}
              />
            </FieldGroup>
          </React.Fragment>
        );

      default:
        return null;
    }
  }

  renderCredentials() {
    const { credentials, credentialsError } = this.state;
    const { source, allCredentials } = this.props;

    const sourceType = _.get(source, apiTypes.API_SOURCE_TYPE);
    const hasSingleCredential = sourceType === 'vcenter' || sourceType === 'satellite';

    const availableCredentials = allCredentials
      .filter(credential => credential.cred_type === sourceType)
      .map(credential => ({ title: credential.name, value: credential.id }));

    let titleAddSelect;
    let title;

    if (!title || !credentials.length) {
      titleAddSelect = availableCredentials.length ? 'Select' : 'Add';
      title = hasSingleCredential ? `${titleAddSelect} a credential` : `${titleAddSelect} one or more credentials`;
    }

    return (
      <FieldGroup label="Credentials" error={credentialsError} errorMessage={credentialsError}>
        <Form.InputGroup>
          <DropdownSelect
            title={(!credentials.length && title) || ''}
            id="credential-select"
            disabled={!availableCredentials.length}
            multiselect={!hasSingleCredential}
            onSelect={this.onChangeCredential}
            options={availableCredentials}
            selectValue={credentials}
            key={`dropdown-update-${availableCredentials.length}`}
          />
          <Form.InputGroup.Button>
            <Button onClick={this.onClickCredential} title="Add a credential">
              <span className="sr-only">Add</span>
              <Icon type="fa" name="plus" />
            </Button>
          </Form.InputGroup.Button>
        </Form.InputGroup>
      </FieldGroup>
    );
  }

  renderOptions() {
    const { sslCertVerify } = this.state;
    const { source } = this.props;

    const sourceType = _.get(source, apiTypes.API_SOURCE_TYPE);

    switch (sourceType) {
      case 'vcenter':
      case 'satellite':
        return (
          <FieldGroup label="Options">
            <div className="quipucords-checkbox">
              <Checkbox checked={sslCertVerify} bsClass="" onChange={this.onChangeSslCertVerify}>
                &nbsp; Verify SSL Certificate
              </Checkbox>
            </div>
          </FieldGroup>
        );
      default:
        return null;
    }
  }

  render() {
    const { sourceName, sourceNameError } = this.state;
    const { source } = this.props;

    const sourceTypeString = helpers.sourceTypeString(_.get(source, apiTypes.API_SOURCE_TYPE));

    return (
      <Form horizontal>
        <FieldGroup label="Name" error={sourceNameError} errorMessage={sourceNameError}>
          <Form.FormControl
            type="text"
            name="sourceName"
            value={sourceName}
            placeholder={`Enter a name for the ${sourceTypeString} source`}
            onChange={this.onChangeSourceName}
          />
        </FieldGroup>
        {this.renderHosts()}
        {this.renderCredentials()}
        {this.renderOptions()}
      </Form>
    );
  }
}

AddSourceWizardStepTwo.propTypes = {
  getWizardCredentials: PropTypes.func,
  source: PropTypes.object,
  allCredentials: PropTypes.array
};

AddSourceWizardStepTwo.defaultProps = {
  getWizardCredentials: helpers.noop,
  source: {},
  allCredentials: []
};

const mapDispatchToProps = dispatch => ({
  getWizardCredentials: () => dispatch(reduxActions.credentials.getWizardCredentials())
});

const mapStateToProps = state => ({ ...state.addSourceWizard.view });

const ConnectedAddSourceWizardStepTwo = connect(
  mapStateToProps,
  mapDispatchToProps
)(AddSourceWizardStepTwo);

export { ConnectedAddSourceWizardStepTwo as default, ConnectedAddSourceWizardStepTwo, AddSourceWizardStepTwo };
