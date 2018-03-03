import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { SplitButton, MenuItem, Checkbox, Button, Icon, Form } from 'patternfly-react';
import Store from '../../redux/store';
import helpers from '../../common/helpers';
import { addSourceWizardField as FieldGroup } from './addSourceWizardField';
import { apiTypes } from '../../constants';
import { sourcesTypes, credentialsTypes } from '../../redux/constants';
import { getWizardCredentials } from '../../redux/actions/credentialsActions';
import _ from 'lodash';

class AddSourceWizardStepTwo extends React.Component {
  constructor(props) {
    super(props);

    this.initialState = {
      source: {},
      stepOneValid: false,

      sourceType: '',
      sourceName: '',
      sourceNameError: null,
      multiHostDisplay: '',
      hosts: [],
      hostsError: null,
      credentials: [],
      credentialsError: null,
      port: '',
      portError: null,
      singleHostPort: '',
      singleHostPortError: null,
      satelliteVersion: '',
      satelliteVersionError: null,
      sslProtocol: '',
      sslProtocolError: null,
      sslCertVerify: '',
      sslCertVerifyError: null,
      disableSsl: '',
      disableSslError: null
    };

    this.state = { ...this.initialState, ...this.initializeState(props) };

    helpers.bindMethods(this, [
      'onChangeSourceName',
      'onChangeCredential',
      'onClickCredential',
      'onChangeHost',
      'onChangeHosts',
      'onChangePort'
    ]);
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps.source && !this.props.source) {
      this.setState(this.initializeState(nextProps));
    } else if (
      _.get(nextProps, `source.${apiTypes.API_SOURCE_TYPE}`) !== _.get(this.props, `source.${apiTypes.API_SOURCE_TYPE}`)
    ) {
      this.setState({ sourceType: _.get(nextProps, `source.${apiTypes.API_SOURCE_TYPE}`) });
    }
  }

  componentDidMount() {
    this.props.getWizardCredentials();
  }

  credentialInfo(id) {
    const { allCredentials } = this.props;
    return _.find(allCredentials, { id: id }) || {};
  }

  initializeState(nextProps) {
    if (nextProps.source) {
      let credentials = _.get(nextProps.source, apiTypes.API_SOURCE_CREDENTIALS, []);

      return {
        sourceType: _.get(nextProps.source, apiTypes.API_SOURCE_TYPE, ''),
        sourceName: _.get(nextProps.source, apiTypes.API_SOURCE_NAME, ''),
        multiHostDisplay: _.get(nextProps.source, apiTypes.API_SOURCE_HOSTS, []).join(',\n'),
        hosts: _.get(nextProps.source, apiTypes.API_SOURCE_HOSTS, []),
        port: _.get(nextProps.source, apiTypes.API_SOURCE_PORT, ''),
        satelliteVersion: _.get(nextProps.source, apiTypes.API_SOURCE_SAT_VERSION, ''),
        sslProtocol: _.get(nextProps.source, apiTypes.API_SOURCE_SSL_PROTOCOL, ''),
        sslCertVerify: _.get(nextProps.source, apiTypes.API_SOURCE_SSL_CERT, ''),
        disableSsl: _.get(nextProps.source, apiTypes.API_SOURCE_SSL_DISABLE, ''),
        singleHostPort: _.get(nextProps.source, apiTypes.API_SOURCE_HOSTS, []).length
          ? `${nextProps.source[apiTypes.API_SOURCE_HOSTS][0]}:${nextProps.source[apiTypes.API_SOURCE_PORT]}`
          : '',
        credentials: credentials.map(val => val.id)
      };
    }

    return {};
  }

  validateStep() {
    const {
      sourceType,
      sourceName,
      sourceNameError,
      hosts,
      hostsError,
      port,
      portError,
      credentials,
      credentialsError,
      satelliteVersion,
      sslProtocol,
      sslCertVerify,
      disableSsl
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
      let updatedSource = { id: source.id };
      _.set(updatedSource, apiTypes.API_SOURCE_TYPE, sourceType);
      _.set(updatedSource, apiTypes.API_SOURCE_NAME, sourceName);
      _.set(updatedSource, apiTypes.API_SOURCE_HOSTS, hosts);
      _.set(updatedSource, apiTypes.API_SOURCE_SAT_VERSION, satelliteVersion);
      _.set(updatedSource, apiTypes.API_SOURCE_SSL_PROTOCOL, sslProtocol);
      _.set(updatedSource, apiTypes.API_SOURCE_SSL_CERT, sslCertVerify);
      _.set(updatedSource, apiTypes.API_SOURCE_SSL_DISABLE, disableSsl);
      _.set(updatedSource, apiTypes.API_SOURCE_CREDENTIALS, credentials);
      if (port !== '') {
        updatedSource[apiTypes.API_SOURCE_PORT] = port;
      }

      Store.dispatch({
        type: sourcesTypes.UPDATE_SOURCE_WIZARD_STEPTWO,
        source: updatedSource
      });
    }
  }

  validateSourceName(value) {
    if (value === '') {
      return 'You must enter a source name';
    }

    return null;
  }

  onChangeSourceName(event) {
    this.setState(
      {
        sourceName: event.target.value,
        sourceNameError: this.validateSourceName(event.target.value)
      },
      () => this.validateStep()
    );
  }

  validateCredentials(value) {
    if (!value.length) {
      return 'You must add a credential';
    }

    return null;
  }

  onChangeCredential(event, value) {
    const { sourceType, credentials } = this.state;
    let submitCreds = [];

    if (sourceType === 'vcenter' || sourceType === 'satellite') {
      submitCreds = [value.id];
    } else {
      submitCreds = [...credentials];
      let credentialIndex = submitCreds.indexOf(value.id);

      if (credentialIndex < 0) {
        submitCreds.push(value.id);
      } else {
        submitCreds.splice(credentialIndex, 1);
      }
    }

    this.setState({ credentials: submitCreds, credentialsError: this.validateCredentials(submitCreds) }, () =>
      this.validateStep()
    );
  }

  onClickCredential() {
    const { sourceType } = this.state;

    Store.dispatch({
      type: credentialsTypes.CREATE_CREDENTIAL_SHOW,
      credentialType: sourceType === 'import' ? 'network' : sourceType
    });
  }

  validateHosts(value) {
    let validation = null;

    if (value.length) {
      _.each(value, host => {
        if (host !== '' && !new RegExp('^\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}$').test(host)) {
          validation = 'You must enter a valid IP address';
          return false;
        }
      });
    }

    return validation;
  }

  validateHost(value) {
    if (!new RegExp('^\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.(\\d{1,3}|[\\d:\\[\\]\\/]+)$').test(value)) {
      return 'You must enter an IP address';
    }

    return null;
  }

  validatePort(value) {
    if (value && value.length && !/^\d{1,4}$/.test(value)) {
      return 'Port must be valid';
    }

    return null;
  }

  onChangePort(event) {
    const value = event.target.value;

    this.setState(
      {
        port: value,
        portError: this.validatePort(value)
      },
      () => this.validateStep()
    );
  }

  onChangeHost(event) {
    let value = event.target.value;
    let host = [];
    let port;
    let hostPort;
    let validateHost;
    let validatePort;

    if (value !== '') {
      hostPort = value.split(':');
      host = [hostPort[0]];
      port = hostPort[1];
    }

    validateHost = this.validateHost(host);
    validatePort = port ? this.validatePort(port) : null;

    this.setState(
      {
        singleHostPort: value,
        singleHostPortError: validateHost || validatePort || null,
        hosts: host,
        hostsError: validateHost,
        port: port || '',
        portError: validatePort
      },
      () => this.validateStep()
    );
  }

  onChangeHosts(event) {
    const value = event.target.value;
    let hosts = [];

    if (value !== '') {
      hosts = value.replace(/\\n|\\r|\s/g, '').split(',');
      hosts = hosts.filter(host => host !== '');
    }

    this.setState(
      {
        multiHostDisplay: value,
        hosts: hosts,
        hostsError: this.validateHosts(hosts)
      },
      () => this.validateStep()
    );
  }

  renderHosts() {
    const {
      sourceType,
      hostsError,
      port,
      portError,
      multiHostDisplay,
      singleHostPort,
      singleHostPortError
    } = this.state;

    switch (sourceType) {
      case 'network':
        return (
          <React.Fragment>
            <FieldGroup label={'Search Addresses'} error={hostsError} errorMessage={hostsError}>
              <Form.FormControl
                componentClass="textarea"
                name="hosts"
                value={multiHostDisplay}
                rows={5}
                placeholder="Enter IP addresses"
                onChange={this.onChangeHosts}
              />
              <Form.HelpBlock>Comma separated, IP ranges, dns, and wildcards are valid.</Form.HelpBlock>
            </FieldGroup>
            <FieldGroup label={'Port'} error={portError} errorMessage={portError}>
              <Form.FormControl
                name="port"
                type="text"
                value={port}
                placeholder="Enter a port"
                onChange={this.onChangePort}
              />
            </FieldGroup>
          </React.Fragment>
        );

      case 'vcenter':
      case 'satellite':
        return (
          <React.Fragment>
            <FieldGroup label={'IP Address:Port'} error={singleHostPortError} errorMessage={singleHostPortError}>
              <Form.FormControl
                name="hosts"
                type="text"
                value={singleHostPort}
                placeholder="Enter an IP address:port"
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
    const { sourceType, credentials, credentialsError } = this.state;
    const { allCredentials } = this.props;

    const hasSingleCredential = sourceType === 'vcenter' || sourceType === 'satellite';

    const availableCredentials = allCredentials.filter(credential => {
      return credential.cred_type === sourceType;
    });
    let titleAddSelect;
    let title;

    if (credentials.length) {
      const selectedCredNames = credentials.map(credential => this.credentialInfo(credential).name);
      title = selectedCredNames.join(', ');
    }

    if (!title || !credentials.length) {
      titleAddSelect = availableCredentials.length ? 'Select' : 'Add';
      title = hasSingleCredential ? `${titleAddSelect} a credential` : `${titleAddSelect} one or more credentials`;
    }

    return (
      <FieldGroup label={'Credentials'} error={credentialsError} errorMessage={credentialsError}>
        <Form.InputGroup>
          <div className="form-split-button">
            <SplitButton
              className="form-control"
              bsStyle="default"
              id="credential-select"
              disabled={!availableCredentials.length}
              title={title}
            >
              {availableCredentials.length &&
                availableCredentials.map((value, index) => {
                  return (
                    <MenuItem key={value.id} eventKey={index} onClick={e => this.onChangeCredential(e, value)}>
                      {!hasSingleCredential && (
                        <Checkbox inline readOnly value={value.id} checked={credentials.indexOf(value.id) > -1}>
                          {value.name}
                        </Checkbox>
                      )}
                      {hasSingleCredential && value.name}
                    </MenuItem>
                  );
                })}
            </SplitButton>
          </div>
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

  render() {
    const { sourceName, sourceNameError } = this.state;

    return (
      <Form horizontal>
        <FieldGroup label={'Name'} error={sourceNameError} errorMessage={sourceNameError}>
          <Form.FormControl
            type="text"
            name="sourceName"
            value={sourceName}
            placeholder="Enter a source name"
            onChange={this.onChangeSourceName}
          />
        </FieldGroup>
        {this.renderHosts()}
        {this.renderCredentials()}
      </Form>
    );
  }
}

AddSourceWizardStepTwo.propTypes = {
  getWizardCredentials: PropTypes.func,
  source: PropTypes.object,
  allCredentials: PropTypes.array
};

const mapDispatchToProps = (dispatch, ownProps) => ({
  getWizardCredentials: () => dispatch(getWizardCredentials())
});

const mapStateToProps = function(state) {
  return Object.assign({}, state.addSourceWizard.view);
};

export default connect(mapStateToProps, mapDispatchToProps)(AddSourceWizardStepTwo);
