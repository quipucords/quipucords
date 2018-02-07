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
  addCredential,
  getCredentials,
  updateCredential
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

    helpers.bindMethods(this, [
      'cancel',
      'save',
      'addResultsCallback',
      'updateResultsCallback'
    ]);
  }

  componentWillReceiveProps(nextProps) {
    if (!this.props.show && nextProps.show) {
      this.resetIntialState(nextProps);
    }

    if (nextProps.show) {
      if (
        nextProps.editing &&
        nextProps.updateFulfilled &&
        nextProps.editCredential
      ) {
        this.updateResultsCallback(false, nextProps.editCredential);
      } else if (nextProps.editing && nextProps.updateError) {
        this.updateResultsCallback(
          nextProps.updateError,
          nextProps.updateErrorMessage
        );
      } else if (nextProps.addFulfilled && nextProps.newCredential) {
        this.addResultsCallback(false, nextProps.newCredential);
      } else if (nextProps.addError) {
        this.addResultsCallback(nextProps.addError, nextProps.addErrorMessage);
      }
    }
  }

  resetIntialState(nextProps) {
    if (nextProps && nextProps.editing && nextProps.editCredential) {
      this.setState({
        credentialName: nextProps.editCredential.name,
        credType: nextProps.editCredential.cred_type,
        authorizationType:
          nextProps.editCredential.ssh_keyfile &&
          nextProps.editCredential.ssh_keyfile.length
            ? 'usernamePassword'
            : 'sshKey',
        sshKeyFile: nextProps.editCredential.ssh_keyfile,
        passphrase: nextProps.editCredential.passphrase,
        username: nextProps.editCredential.username,
        password: nextProps.editCredential.password,
        becomeMethod: nextProps.editCredential.become_method,
        becomeUser: nextProps.editCredential.become_user,
        becomePassword: nextProps.editCredential.become_password,
        credentialNameError: '',
        usernameError: '',
        sskKeyFileError: '',
        becomeUserError: ''
      });
    } else {
      this.setState({
        credentialName: '',
        credType: nextProps.newCredentialType,
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
  }

  cancel() {
    if (this.props.editing) {
      Store.dispatch({
        type: credentialsTypes.EDIT_CREDENTIAL_HIDE
      });
    } else {
      Store.dispatch({
        type: credentialsTypes.CREATE_CREDENTIAL_HIDE
      });
    }
  }

  updateResultsCallback(isError, results) {
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
            Credential <strong>{results.name}</strong> successfully updated.
          </span>
        )
      });
      Store.dispatch({
        type: credentialsTypes.EDIT_CREDENTIAL_HIDE
      });
      this.props.getCredentials();
    }
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
      username: this.state.username,
      cred_type: this.state.credType
    };

    if (this.props.editing) {
      credential.id = this.props.editCredential.id;
    }

    if (this.state.authorizationType === 'sshKey') {
      credential.ssh_keyfile = this.state.sshKeyFile;
    } else {
      credential.password = this.state.password;
    }

    if (credential.cred_type === 'network') {
      credential.become_method = this.state.becomeMethod;
      credential.become_user = this.state.becomeUser;
      credential.become_password = this.state.becomePassword;
    }

    if (this.props.editing) {
      this.props.updateCredential(credential.id, credential);
    } else {
      this.props.addCredential(credential);
    }
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
    const {
      credType,
      becomeMethod,
      becomeUser,
      becomePassword,
      becomeUserError
    } = this.state;

    if (credType !== 'network') {
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
    const { show, editing } = this.props;
    const {
      credType,
      credentialName,
      authorizationType,
      username,
      credentialNameError,
      usernameError
    } = this.state;

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
          <Modal.Title>
            {editing
              ? 'Edit Credential - ' + credentialName
              : 'Create Credential'}
          </Modal.Title>
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
                  value={helpers.sourceTypeString(credType)}
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
                  className="quipucords-form-control"
                  readOnly={editing}
                  placeholder="Enter the new credential name"
                  autoFocus={!editing}
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
            autoFocus={editing}
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

CreateCredentialDialog.propTypes = {
  show: PropTypes.bool,
  editing: PropTypes.bool,

  getCredentials: PropTypes.func,
  credentials: PropTypes.array,

  newCredential: PropTypes.object,
  newCredentialType: PropTypes.string, // eslint-disable-line react/no-unused-prop-types
  addCredential: PropTypes.func,
  addFulfilled: PropTypes.bool,
  addError: PropTypes.bool,
  addErrorMessage: PropTypes.string,

  editCredential: PropTypes.object,
  updateCredential: PropTypes.func,
  updateFulfilled: PropTypes.bool,
  updateError: PropTypes.bool,
  updateErrorMessage: PropTypes.string
};

const mapDispatchToProps = (dispatch, ownProps) => ({
  getCredentials: () => dispatch(getCredentials()),
  addCredential: data => dispatch(addCredential(data)),
  updateCredential: (id, data) => dispatch(updateCredential(id, data))
});

const mapStateToProps = function(state) {
  return Object.assign({}, state.credentials, {
    show:
      state.credentials.showCreateDialog || state.credentials.showEditDialog,
    editing: state.credentials.showEditDialog
  });
};

export default connect(mapStateToProps, mapDispatchToProps)(
  CreateCredentialDialog
);
