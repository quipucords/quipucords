import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { Modal, Alert, Button, Icon, Form, Grid } from 'patternfly-react';
import Store from '../../redux/store';
import { helpers } from '../../common/helpers';
import { authDictionary, dictionary } from '../../constants/dictionaryConstants';
import { credentialsTypes, toastNotificationTypes, viewTypes } from '../../redux/constants';
import { reduxActions } from '../../redux/actions';
import DropdownSelect from '../dropdownSelect/dropdownSelect';

class CreateCredentialDialog extends React.Component {
  static renderFormLabel(label) {
    return (
      <Grid.Col componentClass={Form.ControlLabel} sm={5}>
        {label}
      </Grid.Col>
    );
  }

  static validateCredentialName(credentialName) {
    if (!credentialName) {
      return 'You must enter a credential name';
    }

    if (credentialName.length > 64) {
      return 'The credential name can only contain up to 64 characters';
    }

    return '';
  }

  static validateUsername(username) {
    if (!username || !username.length) {
      return 'You must enter a user name';
    }

    return '';
  }

  static validatePassword(password) {
    if (!password || !password.length) {
      return 'You must enter a password';
    }

    return '';
  }

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
      becomeUserError: '',
      sshKeyDisabled: false
    };

    this.state = { ...this.initialState };

    this.sshKeyFileValidator = new RegExp(/^\/.*$/);

    this.becomeMethods = ['sudo', 'su', 'pbrun', 'pfexec', 'doas', 'dzdo', 'ksu', 'runas'];
  }

  componentWillReceiveProps(nextProps) {
    const { edit, fulfilled, getCredentials, show, viewOptions } = this.props;

    if (!show && nextProps.show) {
      this.resetInitialState(nextProps);
    }

    if (show && nextProps.fulfilled && !fulfilled) {
      Store.dispatch({
        type: toastNotificationTypes.TOAST_ADD,
        alertType: 'success',
        message: (
          <span>
            Credential <strong>{nextProps.credential.name}</strong> successfully
            {edit ? ' updated' : ' added'}.
          </span>
        )
      });

      this.onCancel();
      getCredentials(helpers.createViewQueryObject(viewOptions));
    }
  }

  onCancel = () => {
    Store.dispatch({
      type: credentialsTypes.UPDATE_CREDENTIAL_HIDE
    });
  };

  onSave = () => {
    const { addCredential, credential, edit, updateCredential } = this.props;
    const {
      authorizationType,
      becomeMethod,
      becomePassword,
      becomeUser,
      credentialName,
      credentialType,
      passphrase,
      password,
      sshKeyFile,
      username
    } = this.state;

    const submitCredential = {
      username,
      name: credentialName
    };

    if (edit) {
      submitCredential.id = credential.id;
    } else {
      submitCredential.cred_type = credentialType;
    }

    if (authorizationType === 'sshKey') {
      submitCredential.ssh_keyfile = sshKeyFile;
      submitCredential.sshpassphrase = passphrase;
    } else {
      submitCredential.password = password;
    }

    if (credentialType === 'network') {
      submitCredential.become_method = becomeMethod;
      if (becomeUser) {
        submitCredential.become_user = becomeUser;
      }
      if (becomePassword) {
        submitCredential.become_password = becomePassword;
      }
    }

    if (edit) {
      updateCredential(submitCredential.id, submitCredential);
    } else {
      addCredential(submitCredential);
    }
  };

  onSetAuthType = authType => {
    this.setState({ authorizationType: authType.value });
  };

  onUpdateCredentialName = event => {
    this.setState({
      credentialName: event.target.value,
      credentialNameError: CreateCredentialDialog.validateCredentialName(event.target.value)
    });
  };

  onUpdateUsername = event => {
    this.setState({
      username: event.target.value,
      usernameError: CreateCredentialDialog.validateUsername(event.target.value)
    });
  };

  onUpdatePassword = event => {
    this.setState({
      password: event.target.value,
      passwordError: CreateCredentialDialog.validatePassword(event.target.value)
    });
  };

  onUpdateSshKeyFile = event => {
    this.setState({
      sshKeyFile: event.target.value,
      sskKeyFileError: this.validateSshKeyFile(event.target.value)
    });
  };

  onUpdatePassphrase = event => {
    this.setState({
      passphrase: event.target.value
    });
  };

  onSetBecomeMethod = method => {
    this.setState({
      becomeMethod: method.value
    });
  };

  onUpdateBecomeUser = event => {
    this.setState({
      becomeUser: event.target.value
    });
  };

  onUpdateBecomePassword = event => {
    this.setState({
      becomePassword: event.target.value
    });
  };

  onErrorDismissed = () => {
    Store.dispatch({
      type: credentialsTypes.RESET_CREDENTIAL_UPDATE_STATUS
    });
  };

  resetInitialState(nextProps) {
    let sshKeyDisabled = true;

    if (nextProps.edit && nextProps.credential) {
      if (nextProps.credential.cred_type === 'network' || nextProps.credential.ssh_keyfile) {
        sshKeyDisabled = false;
      }

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
        becomeUserError: '',
        sshKeyDisabled
      });
    } else {
      if (nextProps.credentialType === 'network') {
        sshKeyDisabled = false;
      }

      this.setState({
        ...this.initialState,
        credentialType: nextProps.credentialType,
        sshKeyDisabled
      });
    }
  }

  validateForm() {
    const {
      credentialName,
      credentialNameError,
      username,
      usernameError,
      authorizationType,
      password,
      passwordError,
      sshKeyFile,
      sskKeyFileError
    } = this.state;

    return (
      credentialName &&
      !credentialNameError &&
      username &&
      !usernameError &&
      (authorizationType === 'usernamePassword' ? password && !passwordError : sshKeyFile && !sskKeyFileError)
    );
  }

  validateSshKeyFile(keyFile) {
    if (!this.sshKeyFileValidator.test(keyFile)) {
      return 'Please enter the full path to the SSH Key File';
    }

    return '';
  }

  renderAuthForm() {
    const {
      authorizationType,
      password,
      sshKeyFile,
      passphrase,
      passwordError,
      sskKeyFileError,
      sshKeyDisabled
    } = this.state;

    switch (authorizationType) {
      case 'usernamePassword':
        return (
          <Form.FormGroup validationState={passwordError ? 'error' : null}>
            {CreateCredentialDialog.renderFormLabel('Password')}
            <Grid.Col sm={7}>
              <Form.FormControl
                type="password"
                value={password}
                placeholder="Enter Password"
                onChange={e => this.onUpdatePassword(e)}
              />
              {passwordError && <Form.HelpBlock>{passwordError}</Form.HelpBlock>}
            </Grid.Col>
          </Form.FormGroup>
        );
      case 'sshKey':
        if (sshKeyDisabled) {
          return null;
        }

        return (
          <React.Fragment>
            <Form.FormGroup validationState={sskKeyFileError ? 'error' : null}>
              {CreateCredentialDialog.renderFormLabel('SSH Key File')}
              <Grid.Col sm={7}>
                <Form.FormControl
                  type="text"
                  value={sshKeyFile}
                  placeholder="Enter the full path to the SSH key file"
                  onChange={e => this.onUpdateSshKeyFile(e)}
                />
                {sskKeyFileError && <Form.HelpBlock>{sskKeyFileError}</Form.HelpBlock>}
              </Grid.Col>
            </Form.FormGroup>
            <Form.FormGroup>
              {CreateCredentialDialog.renderFormLabel('Passphrase')}
              <Grid.Col sm={7}>
                <Form.FormControl
                  type="password"
                  value={passphrase}
                  placeholder="optional"
                  onChange={e => this.onUpdatePassphrase(e)}
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
          {CreateCredentialDialog.renderFormLabel('Become Method')}
          <Grid.Col sm={7}>
            <DropdownSelect
              id="become-method-select"
              multiselect={false}
              onSelect={this.onSetBecomeMethod}
              selectValue={becomeMethod}
              options={this.becomeMethods}
            />
          </Grid.Col>
        </Form.FormGroup>
        <Form.FormGroup validationState={becomeUserError ? 'error' : null}>
          {CreateCredentialDialog.renderFormLabel('Become User')}
          <Grid.Col sm={7}>
            <Form.FormControl
              type="text"
              placeholder="optional"
              value={becomeUser}
              onChange={e => this.onUpdateBecomeUser(e)}
            />
          </Grid.Col>
        </Form.FormGroup>
        <Form.FormGroup>
          {CreateCredentialDialog.renderFormLabel('Become Password')}
          <Grid.Col sm={7}>
            <Form.FormControl
              type="password"
              value={becomePassword}
              placeholder="optional"
              onChange={e => this.onUpdateBecomePassword(e)}
            />
          </Grid.Col>
        </Form.FormGroup>
      </React.Fragment>
    );
  }

  renderErrorMessage() {
    const { error, errorMessage } = this.props;

    if (error) {
      return (
        <Alert type="error" onDismiss={this.onErrorDismissed}>
          <strong>Error</strong> {errorMessage}
        </Alert>
      );
    }

    return null;
  }

  render() {
    const { show, edit } = this.props;
    const {
      credentialType,
      credentialName,
      authorizationType,
      username,
      credentialNameError,
      usernameError,
      sshKeyDisabled
    } = this.state;

    return (
      <Modal show={show} onHide={this.onCancel}>
        <Modal.Header>
          <Button className="close" onClick={this.onCancel} aria-hidden="true" aria-label="Close">
            <Icon type="pf" name="close" />
          </Button>
          <Modal.Title>{edit ? `Edit Credential - ${credentialName}` : 'Add Credential'}</Modal.Title>
        </Modal.Header>
        <Modal.Body />
        <Grid fluid>
          {this.renderErrorMessage()}
          <Form horizontal>
            <Form.FormGroup>
              {CreateCredentialDialog.renderFormLabel('Source Type')}
              <Grid.Col sm={7}>
                <Form.FormControl
                  className="quipucords-form-control"
                  type="text"
                  readOnly
                  value={dictionary[credentialType] || ''}
                />
              </Grid.Col>
            </Form.FormGroup>
            <Form.FormGroup validationState={credentialNameError ? 'error' : null}>
              {CreateCredentialDialog.renderFormLabel('Credential Name')}
              <Grid.Col sm={7}>
                <Form.FormControl
                  type="text"
                  className="quipucords-form-control"
                  placeholder="Enter a name for the credential"
                  autoFocus={!edit}
                  value={credentialName}
                  onChange={e => this.onUpdateCredentialName(e)}
                />
                {credentialNameError && <Form.HelpBlock>{credentialNameError}</Form.HelpBlock>}
              </Grid.Col>
            </Form.FormGroup>
            {!sshKeyDisabled && (
              <Form.FormGroup>
                {CreateCredentialDialog.renderFormLabel('Authentication Type')}
                <Grid.Col sm={7}>
                  <DropdownSelect
                    id="auth-type-select"
                    multiselect={false}
                    onSelect={this.onSetAuthType}
                    options={authDictionary}
                    selectValue={authorizationType}
                  />
                </Grid.Col>
              </Form.FormGroup>
            )}
            <Form.FormGroup validationState={usernameError ? 'error' : null}>
              {CreateCredentialDialog.renderFormLabel('Username')}
              <Grid.Col sm={7}>
                <Form.FormControl
                  type="text"
                  placeholder="Enter Username"
                  value={username}
                  onChange={e => this.onUpdateUsername(e)}
                />
                {usernameError && <Form.HelpBlock>{usernameError}</Form.HelpBlock>}
              </Grid.Col>
            </Form.FormGroup>
            {this.renderAuthForm()}
            {this.renderNetworkForm()}
          </Form>
        </Grid>
        <Modal.Footer>
          <Button bsStyle="default" className="btn-cancel" autoFocus={edit} onClick={this.onCancel}>
            Cancel
          </Button>
          <Button bsStyle="primary" onClick={this.onSave} disabled={!this.validateForm()}>
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

CreateCredentialDialog.defaultProps = {
  addCredential: helpers.noop,
  getCredentials: helpers.noop,
  updateCredential: helpers.noop,
  credential: {},
  credentialType: null, // eslint-disable-line react/no-unused-prop-types
  show: false,
  edit: false,
  fulfilled: false,
  error: false,
  errorMessage: null,
  viewOptions: {}
};

const mapDispatchToProps = dispatch => ({
  getCredentials: queryObj => dispatch(reduxActions.credentials.getCredentials(queryObj)),
  addCredential: data => dispatch(reduxActions.credentials.addCredential(data)),
  updateCredential: (id, data) => dispatch(reduxActions.credentials.updateCredential(id, data))
});

const mapStateToProps = state =>
  Object.assign({}, state.credentials.update, {
    viewOptions: state.viewOptions[viewTypes.CREDENTIALS_VIEW]
  });

const ConnectedCreateCredentialDialog = connect(
  mapStateToProps,
  mapDispatchToProps
)(CreateCredentialDialog);

export { ConnectedCreateCredentialDialog as default, ConnectedCreateCredentialDialog, CreateCredentialDialog };
