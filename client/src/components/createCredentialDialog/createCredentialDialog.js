import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import Store from '../../redux/store';
import { Modal, Alert, Button, Icon, Form, Grid, MenuItem } from 'patternfly-react';
import { helpers } from '../../common/helpers';
import { credentialsTypes, toastNotificationTypes, viewTypes } from '../../redux/constants';
import {
  addCredential,
  getCredentials,
  getWizardCredentials,
  updateCredential
} from '../../redux/actions/credentialsActions';
import DropdownSelect from '../dropdownSelect/dropdownSelect';

class CreateCredentialDialog extends React.Component {
  constructor() {
    super();

    // ToDo: evaluate "sudo" as the default for becomeMethod
    this.initialState = {
      credentialName: '',
      credentialType: '',
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

    this.state = { ...this.initialState };

    this.sshKeyFileValidator = new RegExp(/^\/.*$/);

    this.becomeMethods = ['sudo', 'su', 'pbrun', 'pfexec', 'doas', 'dzdo', 'ksu', 'runas'];

    helpers.bindMethods(this, ['cancel', 'save']);
  }

  componentWillReceiveProps(nextProps) {
    if (!this.props.show && nextProps.show) {
      this.resetInitialState(nextProps);
    }

    if (this.props.show && nextProps.fulfilled && !this.props.fulfilled) {
      Store.dispatch({
        type: toastNotificationTypes.TOAST_ADD,
        alertType: 'success',
        message: (
          <span>
            Credential <strong>{nextProps.credential.name}</strong> successfully
            {this.props.edit ? ' updated' : ' created'}.
          </span>
        )
      });

      this.cancel();
      this.props.getCredentials(helpers.createViewQueryObject(this.props.viewOptions));
    }
  }

  resetInitialState(nextProps) {
    if (nextProps.edit && nextProps.credential) {
      this.setState({
        credentialName: nextProps.credential.name,
        credentialType: nextProps.credential.cred_type,
        authorizationType: nextProps.credential.ssh_keyfile ? 'sshKey' : 'usernamePassword',
        sshKeyFile: nextProps.credential.ssh_keyfile,
        passphrase: nextProps.credential.passphrase,
        username: nextProps.credential.username,
        password: nextProps.credential.password,
        becomeMethod: nextProps.credential.become_method,
        becomeUser: nextProps.credential.become_user,
        becomePassword: nextProps.credential.become_password,
        credentialNameError: '',
        usernameError: '',
        sskKeyFileError: '',
        becomeUserError: ''
      });
    } else {
      this.setState({
        ...this.initialState,
        credentialType: nextProps.credentialType
      });
    }
  }

  cancel() {
    Store.dispatch({
      type: credentialsTypes.UPDATE_CREDENTIAL_HIDE
    });
  }

  save() {
    let credential = {
      username: this.state.username,
      name: this.state.credentialName
    };

    if (this.props.edit) {
      credential.id = this.props.credential.id;
    } else {
      credential.cred_type = this.state.credentialType;
    }

    if (this.state.authorizationType === 'sshKey') {
      credential.ssh_keyfile = this.state.sshKeyFile;
      credential.sshpassphrase = this.state.passphrase;
    } else {
      credential.password = this.state.password;
    }

    if (this.state.credentialType === 'network') {
      credential.become_method = this.state.becomeMethod;
      if (this.state.becomeUser) {
        credential.become_user = this.state.becomeUser;
      }
      if (this.state.becomePassword) {
        credential.become_password = this.state.becomePassword;
      }
    }

    if (this.props.edit) {
      this.props.updateCredential(credential.id, credential);
    } else {
      this.props.addCredential(credential).finally(() => {
        this.props.getWizardCredentials();
      });
    }
  }

  setAuthType(authType) {
    this.setState({ authorizationType: authType });
  }

  validateForm() {
    return (
      this.state.credentialName &&
      !this.state.credentialNameError &&
      this.state.username &&
      !this.state.usernameError &&
      (this.state.authorizationType === 'usernamePassword'
        ? this.state.password && !this.state.passwordError
        : this.state.sshKeyFile && !this.state.sskKeyFileError)
    );
  }

  validateCredentialName(credentialName) {
    if (!credentialName) {
      return 'You must enter a credential name';
    }

    if (credentialName.length > 64) {
      return 'The credential name can only contain up to 64 characters';
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

  validatePassword(password) {
    if (!password || !password.length) {
      return 'You must enter a password';
    }

    return '';
  }

  updatePassword(event) {
    this.setState({
      password: event.target.value,
      passwordError: this.validatePassword(event.target.value)
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
    const { authorizationType, password, sshKeyFile, passphrase, passwordError, sskKeyFileError } = this.state;

    switch (authorizationType) {
      case 'usernamePassword':
        return (
          <Form.FormGroup validationState={passwordError ? 'error' : null}>
            {this.renderFormLabel('Password')}
            <Grid.Col sm={7}>
              <Form.FormControl
                type="password"
                value={password}
                placeholder="Enter the password"
                onChange={e => this.updatePassword(e)}
              />
              {passwordError && <Form.HelpBlock>{passwordError}</Form.HelpBlock>}
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
                {sskKeyFileError && <Form.HelpBlock>{sskKeyFileError}</Form.HelpBlock>}
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
    const { credentialType, becomeMethod, becomeUser, becomePassword, becomeUserError } = this.state;

    if (credentialType !== 'network') {
      return null;
    }

    return (
      <React.Fragment>
        <Form.FormGroup>
          {this.renderFormLabel('Become Method')}
          <Grid.Col sm={7}>
            <div className="quipucords-dropdownselect">
              <DropdownSelect
                title={becomeMethod}
                id="become-method-select"
                className="form-control"
                multiselect={false}
              >
                {this.becomeMethods.map((nextMethod, index) => (
                  <MenuItem
                    key={index}
                    className={{ 'quipucords-dropdownselect-menuitem-selected': nextMethod === becomeMethod }}
                    eventKey={`become${index}`}
                    onClick={() => this.setBecomeMethod(nextMethod)}
                  >
                    {nextMethod}
                  </MenuItem>
                ))}
              </DropdownSelect>
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

  errorDismissed() {
    Store.dispatch({
      type: credentialsTypes.RESET_CREDENTIAL_UPDATE_STATUS
    });
  }

  renderErrorMessage() {
    const { error, errorMessage } = this.props;

    if (error) {
      return (
        <Alert type="error" onDismiss={this.errorDismissed}>
          <strong>Error</strong> {errorMessage}
        </Alert>
      );
    } else {
      return null;
    }
  }

  render() {
    const { show, edit } = this.props;
    const {
      credentialType,
      credentialName,
      authorizationType,
      username,
      credentialNameError,
      usernameError
    } = this.state;

    return (
      <Modal show={show} onHide={this.cancel}>
        <Modal.Header>
          <Button className="close" onClick={this.cancel} aria-hidden="true" aria-label="Close">
            <Icon type="pf" name="close" />
          </Button>
          <Modal.Title>{edit ? `Edit Credential - ${credentialName}` : 'Create Credential'}</Modal.Title>
        </Modal.Header>
        <Modal.Body />
        <Grid fluid>
          {this.renderErrorMessage()}
          <Form horizontal>
            <Form.FormGroup>
              {this.renderFormLabel('Source Type')}
              <Grid.Col sm={7}>
                <Form.FormControl
                  className="quipucords-form-control"
                  type="text"
                  readOnly
                  value={helpers.sourceTypeString(credentialType)}
                />
              </Grid.Col>
            </Form.FormGroup>
            <Form.FormGroup validationState={credentialNameError ? 'error' : null}>
              {this.renderFormLabel('Credential Name')}
              <Grid.Col sm={7}>
                <Form.FormControl
                  type="text"
                  className="quipucords-form-control"
                  placeholder="Enter the credential name"
                  autoFocus={!edit}
                  value={credentialName}
                  onChange={e => this.updateCredentialName(e)}
                />
                {credentialNameError && <Form.HelpBlock>{credentialNameError}</Form.HelpBlock>}
              </Grid.Col>
            </Form.FormGroup>
            <Form.FormGroup>
              {this.renderFormLabel('Authentication Type')}
              <Grid.Col sm={7}>
                <div className="quipucords-dropdownselect">
                  <DropdownSelect
                    title={helpers.authorizationTypeString(authorizationType)}
                    id="auth-type-select"
                    className="form-control"
                    multiselect={false}
                  >
                    <MenuItem
                      key="usernamePassword"
                      className={{
                        'quipucords-dropdownselect-menuitem-selected': authorizationType === 'usernamePassword'
                      }}
                      eventKey="1"
                      onClick={() => this.setAuthType('usernamePassword')}
                    >
                      {helpers.authorizationTypeString('usernamePassword')}
                    </MenuItem>
                    <MenuItem
                      key="sshKey"
                      className={{ 'quipucords-dropdownselect-menuitem-selected': authorizationType === 'sshKey' }}
                      eventKey="2"
                      onClick={() => this.setAuthType('sshKey')}
                    >
                      {helpers.authorizationTypeString('sshKey')}
                    </MenuItem>
                  </DropdownSelect>
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
                {usernameError && <Form.HelpBlock>{usernameError}</Form.HelpBlock>}
              </Grid.Col>
            </Form.FormGroup>
            {this.renderAuthForm()}
            {this.renderNetworkForm()}
          </Form>
        </Grid>
        <Modal.Footer>
          <Button bsStyle="default" className="btn-cancel" autoFocus={edit} onClick={this.cancel}>
            Cancel
          </Button>
          <Button bsStyle="primary" onClick={this.save} disabled={!this.validateForm()}>
            Save
          </Button>
        </Modal.Footer>
      </Modal>
    );
  }
}

CreateCredentialDialog.propTypes = {
  addCredential: PropTypes.func,
  getCredentials: PropTypes.func,
  getWizardCredentials: PropTypes.func,
  updateCredential: PropTypes.func,
  credential: PropTypes.object,
  credentialType: PropTypes.string, // eslint-disable-line react/no-unused-prop-types
  show: PropTypes.bool,
  edit: PropTypes.bool,
  fulfilled: PropTypes.bool,
  error: PropTypes.bool,
  errorMessage: PropTypes.string,
  viewOptions: PropTypes.object
};

const mapDispatchToProps = (dispatch, ownProps) => ({
  getCredentials: queryObj => dispatch(getCredentials(queryObj)),
  getWizardCredentials: () => dispatch(getWizardCredentials()),
  addCredential: data => dispatch(addCredential(data)),
  updateCredential: (id, data) => dispatch(updateCredential(id, data))
});

const mapStateToProps = function(state) {
  return Object.assign({}, state.credentials.update, {
    viewOptions: state.viewOptions[viewTypes.CREDENTIALS_VIEW]
  });
};

export default connect(mapStateToProps, mapDispatchToProps)(CreateCredentialDialog);
