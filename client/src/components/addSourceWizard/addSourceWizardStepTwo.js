import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { MenuItem, Button, Icon, Form, Grid } from 'patternfly-react';
import Store from '../../redux/store';
import helpers from '../../common/helpers';
import DropdownSelect from './addSourceWizardDropdownSelect';
import { addSourceWizardField as FieldGroup } from './addSourceWizardField';
import { apiTypes } from '../../constants';
import { sourcesTypes, credentialsTypes } from '../../redux/constants';
import { getWizardCredentials } from '../../redux/actions/credentialsActions';
import _ from 'lodash';

class AddSourceWizardStepTwo extends React.Component {
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
      singleHostPort: '',
      singleHostPortError: null
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
      _.get(nextProps.source, apiTypes.API_SOURCE_TYPE) !== _.get(this.props.source, apiTypes.API_SOURCE_TYPE)
    ) {
      this.setState({ sourceType: _.get(nextProps.source, apiTypes.API_SOURCE_TYPE) });
    }
  }

  componentDidMount() {
    this.props.getWizardCredentials();
  }

  credentialInfo(id) {
    return _.find(this.props.allCredentials, { id: id }) || {};
  }

  initializeState(nextProps) {
    if (nextProps.source) {
      const credentials = _.get(nextProps.source, apiTypes.API_SOURCE_CREDENTIALS, []);
      let singlePort = _.get(nextProps.source, apiTypes.API_SOURCE_PORT);
      let singleHostPort = _.get(nextProps.source, apiTypes.API_SOURCE_HOSTS);

      if (_.get(nextProps.source, apiTypes.API_SOURCE_HOSTS, []).length) {
        singlePort = singlePort ? `:${singlePort}` : '';
        singleHostPort = singleHostPort ? `${nextProps.source[apiTypes.API_SOURCE_HOSTS][0]}${singlePort}` : '';
      }

      return {
        sourceName: _.get(nextProps.source, apiTypes.API_SOURCE_NAME, ''),
        multiHostDisplay: _.get(nextProps.source, apiTypes.API_SOURCE_HOSTS, []).join(',\n'),
        hosts: _.get(nextProps.source, apiTypes.API_SOURCE_HOSTS, []),
        port: _.get(nextProps.source, apiTypes.API_SOURCE_PORT, ''),
        singleHostPort: singleHostPort,
        credentials: credentials.map(val => val.id)
      };
    }

    return {};
  }

  validateStep() {
    const {
      sourceName,
      sourceNameError,
      hosts,
      hostsError,
      port,
      portError,
      credentials,
      credentialsError
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
      let updatedSource = {};

      _.set(updatedSource, apiTypes.API_SOURCE_NAME, sourceName);
      _.set(updatedSource, apiTypes.API_SOURCE_HOSTS, hosts);
      _.set(updatedSource, apiTypes.API_SOURCE_CREDENTIALS, credentials.map(value => parseInt(value, 10)));

      if (port !== '') {
        updatedSource[apiTypes.API_SOURCE_PORT] = port;
      }

      Store.dispatch({
        type: sourcesTypes.UPDATE_SOURCE_WIZARD_STEPTWO,
        source: _.merge({}, source, updatedSource)
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
    const { credentials } = this.state;
    const { source } = this.props;

    let sourceType = _.get(source, apiTypes.API_SOURCE_TYPE);
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
    const { source } = this.props;

    Store.dispatch({
      type: credentialsTypes.CREATE_CREDENTIAL_SHOW,
      credentialType: _.get(source, apiTypes.API_SOURCE_TYPE)
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
    const { hostsError, port, portError, multiHostDisplay, singleHostPort, singleHostPortError } = this.state;
    const { source } = this.props;

    let sourceType = _.get(source, apiTypes.API_SOURCE_TYPE);

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
                placeholder="Default port :22"
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
                placeholder="Enter an IP address (default port :443)"
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

    const availableCredentials = allCredentials.filter(credential => {
      return credential.cred_type === sourceType;
    });

    let titleAddSelect;
    let title;

    if (credentials.length) {
      title = credentials.map(credential => this.credentialInfo(credential).name).join(', ');
    }

    if (!title || !credentials.length) {
      titleAddSelect = availableCredentials.length ? 'Select' : 'Add';
      title = hasSingleCredential ? `${titleAddSelect} a credential` : `${titleAddSelect} one or more credentials`;
    }

    return (
      <FieldGroup label={'Credentials'} error={credentialsError} errorMessage={credentialsError}>
        <Form.InputGroup>
          <div className="quipucords-dropdownselect">
            <DropdownSelect
              title={title}
              id="credential-select"
              disabled={!availableCredentials.length}
              className="form-control"
              multiselect={!hasSingleCredential}
            >
              {availableCredentials.length &&
                availableCredentials.map((value, index) => {
                  return (
                    <MenuItem
                      key={value.id}
                      eventKey={index}
                      className={{ 'quipucords-dropdownselect-menuitem-selected': credentials.indexOf(value.id) > -1 }}
                      onSelect={e => this.onChangeCredential(e, value)}
                    >
                      {!hasSingleCredential && (
                        <Grid.Row className="quipucords-dropdownselect-menuitem">
                          <Grid.Col xs={10} className="quipucords-dropdownselect-menuitemname">
                            {value.name}
                          </Grid.Col>
                          <Grid.Col xs={2} className="quipucords-dropdownselect-menuitemcheck">
                            {credentials.indexOf(value.id) > -1 && <Icon type="fa" name="check" />}
                          </Grid.Col>
                        </Grid.Row>
                      )}
                      {hasSingleCredential && value.name}
                    </MenuItem>
                  );
                })}
            </DropdownSelect>
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
