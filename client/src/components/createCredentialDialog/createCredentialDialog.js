import { connect } from 'react-redux';
import React from 'react';
import PropTypes from 'prop-types';

import {
  Modal,
  Button,
  Icon,
  Form,
  Grid,
  SplitButton,
  MenuItem
} from 'patternfly-react';

import { helpers } from '../../common/helpers';
import Store from '../../redux/store';
import {
  credentialsTypes,
  toastNotificationTypes
} from '../../redux/constants';
import {
  getCredentials,
  addCredential
} from '../../redux/actions/credentialsActions';

const becomeMethods = [
  'sudo',
  'su',
  'pbrun',
  'pfexec',
  'doas',
  'dzdo',
  'ksu',
  'runas'
];

class CreateCredentialDialog extends React.Component {
  constructor() {
    super();

    this.state = {
      credentialName: '',
      authorizationType: 'usernamePassword',
      sshKeyFile: '',
      passphrase: '',
      username: '',
      password: '',
      becomeMethod: 'sudo',
      becomeUser: '',
      becomePassword: '',
      credentialNameError: '',
      usernameError: '',
      sskKeyFileError: '',
      becomeUserError: ''
    };

    this.sshKeyFileValidator = new RegExp(/^\/.*$/);

    helpers.bindMethods(this, ['cancel', 'save', 'addResultsCallback']);
  }

  componentWillReceiveProps(nextProps) {
    if (!this.props.show && nextProps.show) {
      this.resetIntialState();
      this.props.getCredentials();
    }
  }

  resetIntialState() {
    this.setState({
      credentialName: '',
      authorizationType: 'usernamePassword',
      sshKeyFile: '',
      passphrase: '',
      username: '',
      password: '',
      becomeMethod: 'sudo',
      becomeUser: '',
      becomePassword: '',
      credentialNameError: '',
      usernameError: '',
      sskKeyFileError: '',
      becomeUserError: ''
    });
  }

  cancel() {
    Store.dispatch({
      type: credentialsTypes.CREATE_CREDENTIAL_HIDE
    });
  }

  addResultsCallback(isError, results) {
    if (isError) {
      Store.dispatch({
        type: toastNotificationTypes.TOAST_ADD,
        alertType: 'error',
        header: 'Error',
        message: results
      });
    } else {
      Store.dispatch({
        type: toastNotificationTypes.TOAST_ADD,
        alertType: 'success',
        message: (
          <span>
            Credential <strong>{results.name}</strong> successfully created.
          </span>
        )
      });
      Store.dispatch({
        type: credentialsTypes.CREATE_CREDENTIAL_HIDE
      });
      this.props.getCredentials();
    }
  }

  save() {
    let credential = {
      name: this.state.credentialName,
      cred_type: this.props.credentialType,
      username: this.state.username
    };

    if (this.state.authorizationType === 'sshKey') {
      credential.ssh_keyfile = this.state.sshKeyFile;
    } else {
      credential.password = this.state.password;
    }

    if (this.props.credentialType === 'network') {
      credential.become_method = this.state.becomeMethod;
      credential.become_user = this.state.becomeUser;
      credential.become_password = this.state.becomePassword;
    }

    this.props.addCredential(credential, this.addResultsCallback);
  }

  setAuthType(authType) {
    this.setState({ authorizationType: authType });
  }

  validateForm() {
    return (
      this.state.credentialName !== '' &&
      this.state.credentialNameError === '' &&
      this.state.username !== '' &&
      this.state.usernameError === '' &&
      (this.state.authorizationType === 'usernamePassword' ||
        (this.state.sshKeyFile !== '' && this.state.sskKeyFileError === ''))
    );
  }

  nameExists(name) {
    const { credentials } = this.props;
    return (
      credentials &&
      credentials.find(credential => {
        return credential.name === name;
      })
    );
  }

  validateCredentialName(credentialName) {
    if (!credentialName) {
      return 'You must enter a credential name';
    }

    if (credentialName.length > 64) {
      return 'The credential name can only contain up to 64 characters';
    }

    if (this.nameExists(credentialName)) {
      return 'Credential name already exists';
    }

    return '';
  }

  updateCredentialName(event) {
    this.setState({
      credentialName: event.target.value,
      credentialNameError: this.validateCredentialName(event.target.value)
    });
  }

  validateUsername(username) {
    if (!username || !username.length) {
      return 'You must enter a user name';
    }

    return '';
  }

  updateUsername(event) {
    this.setState({
      username: event.target.value,
      usernameError: this.validateUsername(event.target.value)
    });
  }

  updatePassword(event) {
    this.setState({
      password: event.target.value
    });
  }

  validateSshKeyFile(keyFile) {
    if (!this.sshKeyFileValidator.test(keyFile)) {
      return 'Please enter the full path to the SSH Key File';
    }

    return '';
  }

  updateSshKeyFile(event) {
    this.setState({
      sshKeyFile: event.target.value,
      sskKeyFileError: this.validateSshKeyFile(event.target.value)
    });
  }

  updatePassphrase(event) {
    this.setState({
      passphrase: event.target.value
    });
  }

  setBecomeMethod(method) {
    this.setState({
      becomeMethod: method
    });
  }

  updateBecomeUser(event) {
    this.setState({
      becomeUser: event.target.value
    });
  }

  updateBecomePassword(event) {
    this.setState({
      becomePassword: event.target.value
    });
  }

  renderFormLabel(label) {
    return (
      <Grid.Col componentClass={Form.ControlLabel} sm={5}>
        {label}
      </Grid.Col>
    );
  }

  renderAuthForm() {
    const {
      authorizationType,
      password,
      sshKeyFile,
      passphrase,
      sskKeyFileError
    } = this.state;

    switch (authorizationType) {
      case 'usernamePassword':
        return (
          <Form.FormGroup>
            {this.renderFormLabel('Password')}
            <Grid.Col sm={7}>
              <Form.FormControl
                type="password"
                value={password}
                placeholder="optional"
                onChange={e => this.updatePassword(e)}
              />
            </Grid.Col>
          </Form.FormGroup>
        );
      case 'sshKey':
        return (
          <React.Fragment>
            <Form.FormGroup validationState={sskKeyFileError ? 'error' : null}>
              {this.renderFormLabel('SSH Key File')}
              <Grid.Col sm={7}>
                <Form.FormControl
                  type="text"
                  value={sshKeyFile}
                  placeholder="Enter the full path to the SSH key file"
                  onChange={e => this.updateSshKeyFile(e)}
                />
                {sskKeyFileError && (
                  <Form.HelpBlock>{sskKeyFileError}</Form.HelpBlock>
                )}
              </Grid.Col>
            </Form.FormGroup>
            <Form.FormGroup>
              {this.renderFormLabel('Passphrase')}
              <Grid.Col sm={7}>
                <Form.FormControl
                  type="password"
                  value={passphrase}
                  placeholder="optional"
                  onChange={e => this.updatePassphrase(e)}
                />
              </Grid.Col>
            </Form.FormGroup>
          </React.Fragment>
        );
      default:
        return null;
    }
  }

  renderNetworkForm() {
    const { credentialType } = this.props;
    const {
      becomeMethod,
      becomeUser,
      becomePassword,
      becomeUserError
    } = this.state;

    if (credentialType !== 'network') {
      return null;
    }

    return (
      <React.Fragment>
        <Form.FormGroup>
          {this.renderFormLabel('Become Method')}
          <Grid.Col sm={7}>
            <div className="form-split-button">
              <SplitButton
                className="form-control"
                bsStyle="default"
                title={becomeMethod}
                id="become-method-button"
              >
                {becomeMethods.map((nextMethod, index) => (
                  <MenuItem
                    key={index}
                    eventKey={`become${index}`}
                    onClick={() => this.setBecomeMethod(nextMethod)}
                  >
                    {nextMethod}
                  </MenuItem>
                ))}
              </SplitButton>
            </div>
          </Grid.Col>
        </Form.FormGroup>
        <Form.FormGroup validationState={becomeUserError ? 'error' : null}>
          {this.renderFormLabel('Become User')}
          <Grid.Col sm={7}>
            <Form.FormControl
              type="text"
              placeholder="optional"
              value={becomeUser}
              onChange={e => this.updateBecomeUser(e)}
            />
          </Grid.Col>
        </Form.FormGroup>
        <Form.FormGroup>
          {this.renderFormLabel('Become Password')}
          <Grid.Col sm={7}>
            <Form.FormControl
              type="password"
              value={becomePassword}
              placeholder="optional"
              onChange={e => this.updateBecomePassword(e)}
            />
          </Grid.Col>
        </Form.FormGroup>
      </React.Fragment>
    );
  }

  render() {
    const { show, credentialType } = this.props;
    const {
      credentialName,
      authorizationType,
      username,
      credentialNameError,
      usernameError
    } = this.state;

    let credentialTypeText;

    switch (credentialType) {
      case 'vcenter':
        credentialTypeText = 'VCenter';
        break;
      case 'network':
        credentialTypeText = 'Network';
        break;
      case 'satellite':
        credentialTypeText = 'Satellite';
        break;
      default:
        credentialTypeText = '';
    }

    return (
      <Modal show={show} onHide={this.cancel}>
        <Modal.Header>
          <Button
            className="close"
            onClick={this.cancel}
            aria-hidden="true"
            aria-label="Close"
          >
            <Icon type="pf" name="close" />
          </Button>
          <Modal.Title>Create Credential</Modal.Title>
        </Modal.Header>
        <Modal.Body />
        <Grid fluid>
          <Form horizontal>
            <Form.FormGroup>
              {this.renderFormLabel('Source Type')}
              <Grid.Col sm={7}>
                <Form.FormControl
                  className="quipucords-form-control"
                  type="text"
                  readOnly
                  value={credentialTypeText}
                />
              </Grid.Col>
            </Form.FormGroup>
            <Form.FormGroup
              validationState={credentialNameError ? 'error' : null}
            >
              {this.renderFormLabel('Credential Name')}
              <Grid.Col sm={7}>
                <Form.FormControl
                  type="text"
                  placeholder="Enter the new credential name"
                  autoFocus
                  value={credentialName}
                  onChange={e => this.updateCredentialName(e)}
                />
                {credentialNameError && (
                  <Form.HelpBlock>{credentialNameError}</Form.HelpBlock>
                )}
              </Grid.Col>
            </Form.FormGroup>
            <Form.FormGroup>
              {this.renderFormLabel('Authentication Type')}
              <Grid.Col sm={7}>
                <div className="form-split-button">
                  <SplitButton
                    className="form-control"
                    bsStyle="default"
                    title={helpers.authorizationTypeString(authorizationType)}
                    id="auth-type-button"
                  >
                    <MenuItem
                      eventKey="1"
                      onClick={() => this.setAuthType('usernamePassword')}
                    >
                      {helpers.authorizationTypeString('usernamePassword')}
                    </MenuItem>
                    <MenuItem
                      eventKey="2"
                      onClick={() => this.setAuthType('sshKey')}
                    >
                      {helpers.authorizationTypeString('sshKey')}
                    </MenuItem>
                  </SplitButton>
                </div>
              </Grid.Col>
            </Form.FormGroup>
            <Form.FormGroup validationState={usernameError ? 'error' : null}>
              {this.renderFormLabel('Username')}
              <Grid.Col sm={7}>
                <Form.FormControl
                  type="text"
                  placeholder="Enter the username"
                  value={username}
                  onChange={e => this.updateUsername(e)}
                />
                {usernameError && (
                  <Form.HelpBlock>{usernameError}</Form.HelpBlock>
                )}
              </Grid.Col>
            </Form.FormGroup>
            {this.renderAuthForm()}
            {this.renderNetworkForm()}
          </Form>
        </Grid>
        <Modal.Footer>
          <Button
            bsStyle="default"
            className="btn-cancel"
            onClick={this.cancel}
          >
            Cancel
          </Button>
          <Button
            bsStyle="primary"
            onClick={this.save}
            disabled={!this.validateForm()}
          >
            Save
          </Button>
        </Modal.Footer>
      </Modal>
    );
  }
}

const mapDispatchToProps = (dispatch, ownProps) => ({
  getCredentials: () => dispatch(getCredentials()),
  addCredential: (data, addCallback) =>
    dispatch(addCredential(data, addCallback))
});

CreateCredentialDialog.propTypes = {
  show: PropTypes.bool,
  credentialType: PropTypes.string,
  credentials: PropTypes.array,
  getCredentials: PropTypes.func,
  addCredential: PropTypes.func
};

function mapStateToProps(state, ownProps) {
  return {
    show: state.credentials.showCreateDialog,
    credentialType: state.credentials.createCredentialType,
    credentials: state.credentials.data
  };
}

export default connect(mapStateToProps, mapDispatchToProps)(
  CreateCredentialDialog
);
