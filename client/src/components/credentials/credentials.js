import PropTypes from 'prop-types';
import React from 'react';
import { connect } from 'react-redux';

import {
  Alert,
  Button,
  DropdownButton,
  EmptyState,
  Form,
  Grid,
  Icon,
  ListView,
  MenuItem,
  Modal
} from 'patternfly-react';

import { getCredentials } from '../../redux/actions/credentialsActions';
import {
  confirmationModalTypes,
  credentialsTypes,
  toastNotificationTypes,
  viewTypes
} from '../../redux/constants';
import Store from '../../redux/store';
import helpers from '../../common/helpers';

import ViewToolbar from '../viewToolbar/viewToolbar';
import ViewPaginationRow from '../viewPaginationRow/viewPaginationRow';

import CredentialsEmptyState from './credentialsEmptyState';
import { CredentialListItem } from './credentialListItem';
import CreateCredentialDialog from '../createCredentialDialog/createCredentialDialog';
import {
  CredentialFilterFields,
  CredentialSortFields
} from './crendentialConstants';

class Credentials extends React.Component {
  constructor() {
    super();

    helpers.bindMethods(this, [
      'addCredential',
      'deleteCredentials',
      'itemSelectChange',
      'editCredential',
      'deleteCredential',
      'addSource',
      'importSources',
      'refresh'
    ]);
    this.state = {
      selectedItems: []
    };
  }

  componentDidMount() {
    this.props.getCredentials(helpers.viewQueryObject(this.props.viewOptions));
  }

  componentWillReceiveProps(nextProps, nextState) {
    if (nextProps.credentials !== this.props.credentials) {
      // Reset selection state though we may want to keep selections over refreshes...
      nextProps.credentials.forEach(credential => {
        credential.selected = false;
        if (credential.ssh_keyfile && credential.ssh_keyfile !== '') {
          credential.auth_type = 'sshKey';
        } else {
          credential.auth_type = 'usernamePassword';
        }
      });

      this.setState({ selectedItems: [] });
    }

    // Check for changes resulting in a fetch
    if (
      helpers.viewPropsChanged(nextProps.viewOptions, this.props.viewOptions)
    ) {
      this.props.getCredentials(helpers.viewQueryObject(nextProps.viewOptions));
    }
  }

  addCredential(credentialType) {
    Store.dispatch({
      type: credentialsTypes.CREATE_CREDENTIAL_SHOW,
      credentialType
    });
  }

  deleteCredentials() {
    const { selectedItems } = this.state;

    let heading = (
      <span>Are you sure you want to delete the following credentials?</span>
    );

    let credentialsList = '';
    selectedItems.forEach((item, index) => {
      return (credentialsList += (index > 0 ? '\n' : '') + item.name);
    });

    let body = (
      <Grid.Col sm={12}>
        <Form.FormControl
          className="quipucords-text-area-output"
          componentClass="textarea"
          type="textarea"
          readOnly
          rows={selectedItems.length}
          value={credentialsList}
        />
      </Grid.Col>
    );

    let onConfirm = () => this.doDeleteCredentials(selectedItems);

    Store.dispatch({
      type: confirmationModalTypes.CONFIRMATION_MODAL_SHOW,
      title: 'Delete Credentials',
      heading: heading,
      body: body,
      confirmButtonText: 'Delete',
      onConfirm: onConfirm
    });
  }

  itemSelectChange(item) {
    const { credentials } = this.props;

    item.selected = !item.selected;
    let selectedItems = credentials.filter(item => {
      return item.selected === true;
    });

    this.setState({ selectedItems: selectedItems });
  }

  editCredential(item) {
    Store.dispatch({
      type: credentialsTypes.EDIT_CREDENTIAL_SHOW,
      credential: item
    });
  }

  doDeleteCredentials(items) {
    Store.dispatch({
      type: confirmationModalTypes.CONFIRMATION_MODAL_HIDE
    });

    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: items[0].name,
      message: 'Deleting credentials is not yet implemented'
    });
  }

  deleteCredential(item) {
    let heading = (
      <span>
        Are you sure you want to delete the credential{' '}
        <strong>{item.name}</strong>?
      </span>
    );

    let onConfirm = () => this.doDeleteCredentials([item]);

    Store.dispatch({
      type: confirmationModalTypes.CONFIRMATION_MODAL_SHOW,
      title: 'Delete Source',
      heading: heading,
      confirmButtonText: 'Delete',
      onConfirm: onConfirm
    });
  }

  addSource() {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: 'NYI',
      message: 'Adding sources is not yet implemented'
    });
  }

  importSources() {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: 'NYI',
      message: 'Importing sources is not yet implemented'
    });
  }

  refresh() {
    this.props.getCredentials();
  }

  renderActions() {
    const { selectedItems } = this.state;

    return (
      <div className="form-group">
        <DropdownButton
          bsStyle="primary"
          title="Create"
          pullRight
          id="createCredentialButton"
        >
          <MenuItem eventKey="1" onClick={() => this.addCredential('network')}>
            Network Credential
          </MenuItem>
          <MenuItem
            eventKey="2"
            onClick={() => this.addCredential('satellite')}
          >
            Satellite Credential
          </MenuItem>
          <MenuItem eventKey="2" onClick={() => this.addCredential('vcenter')}>
            VCenter Credential
          </MenuItem>
        </DropdownButton>
        <Button
          disabled={!selectedItems || selectedItems.length === 0}
          onClick={this.deleteCredentials}
        >
          Delete
        </Button>
        <Button onClick={this.refresh} bsStyle="success">
          <Icon type="fa" name="refresh" />
        </Button>
      </div>
    );
  }

  renderList(items) {
    return (
      <ListView className="quipicords-list-view">
        {items.map((item, index) => (
          <CredentialListItem
            item={item}
            key={index}
            onItemSelectChange={this.itemSelectChange}
            onEdit={this.editCredential}
            onDelete={this.deleteCredential}
          />
        ))}
      </ListView>
    );
  }

  render() {
    const {
      pending,
      error,
      errorMessage,
      credentials,
      viewOptions
    } = this.props;

    if (pending) {
      return (
        <Modal bsSize="lg" backdrop={false} show animation={false}>
          <Modal.Body>
            <div className="spinner spinner-xl" />
            <div className="text-center">Loading credentials...</div>
          </Modal.Body>
        </Modal>
      );
    }

    if (error) {
      return (
        <EmptyState>
          <Alert type="error">
            <span>Error retrieving credentials: {errorMessage}</span>
          </Alert>
        </EmptyState>
      );
    }

    if (credentials && credentials.length) {
      return (
        <React.Fragment>
          <div className="quipucords-view-container">
            <ViewToolbar
              viewType={viewTypes.CREDENTIALS_VIEW}
              filterFields={CredentialFilterFields}
              sortFields={CredentialSortFields}
              actions={this.renderActions()}
              itemsType="Credential"
              itemsTypePlural="Credentials"
              {...viewOptions}
            />
            <div className="quipucords-list-container">
              {this.renderList(credentials)}
            </div>
            <ViewPaginationRow
              viewType={viewTypes.CREDENTIALS_VIEW}
              {...viewOptions}
            />
          </div>
          <CreateCredentialDialog credentials={credentials} />
        </React.Fragment>
      );
    }
    return [
      <CredentialsEmptyState
        key="emptyState"
        onAddCredential={this.addCredential}
        onAddSource={this.addSource}
        onImportSources={this.importSources}
      />,
      <CreateCredentialDialog
        key="createCredentialDialog"
        credentials={credentials}
      />
    ];
  }
}

Credentials.propTypes = {
  getCredentials: PropTypes.func,
  error: PropTypes.bool,
  errorMessage: PropTypes.string,
  pending: PropTypes.bool,
  credentials: PropTypes.array,
  viewOptions: PropTypes.object
};

const mapDispatchToProps = (dispatch, ownProps) => ({
  getCredentials: () => dispatch(getCredentials())
});

const mapStateToProps = function(state) {
  return Object.assign({}, state.credentials.view, state.credentials.persist, {
    viewOptions: state.viewOptions[viewTypes.CREDENTIALS_VIEW]
  });
};

export default connect(mapStateToProps, mapDispatchToProps)(Credentials);
