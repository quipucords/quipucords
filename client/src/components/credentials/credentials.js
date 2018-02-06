import PropTypes from 'prop-types';
import React from 'react';
import { connect } from 'react-redux';

import {
  Alert,
  Form,
  Grid,
  EmptyState,
  Row,
  ListView,
  Modal
} from 'patternfly-react';

import { getCredentials } from '../../redux/actions/credentialsActions';
import Store from '../../redux/store';
import {
  confirmationModalTypes,
  credentialsTypes,
  toastNotificationTypes
} from '../../redux/constants';
import { bindMethods } from '../../common/helpers';

import CredentialsToolbar from './credentialsToolbar';
import CredentialsEmptyState from './credentialsEmptyState';
import { CredentialListItem } from './credentialListItem';
import CreateCredentialDialog from '../createCredentialDialog/createCredentialDialog';

class Credentials extends React.Component {
  constructor() {
    super();

    bindMethods(this, [
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
      filteredItems: [],
      selectedItems: []
    };
  }

  componentDidMount() {
    this.props.getCredentials();
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps.credentials !== this.props.credentials) {
      // Reset selection state though we may want to keep selections over refreshes...
      nextProps.credentials.forEach(credential => {
        credential.selected = false;
        if (credential.ssh_keyfile && credential.ssh_keyfile !== '') {
          credential.auth_type = 'sshKey';
        } else if (credential.become_user && credential.become_user !== '') {
          credential.auth_type = 'becomeUser';
        } else {
          credential.auth_type = 'usernamePassword';
        }
      });

      // TODO: Remove once we get real failed host data
      let failedCount = Math.floor(Math.random() * 10);
      nextProps.credentials.forEach(credential => {
        credential.selected = false;
        credential.failed_hosts = [];
        for (let i = 0; i < failedCount; i++) {
          credential.failed_hosts.push('failedHost' + (i + 1));
        }
      });

      let filteredItems = this.filterCredentials(
        nextProps.credentials,
        nextProps.activeFilters
      );

      this.setState({ filteredItems: filteredItems, selectedItems: [] });
    } else if (nextProps.activeFilters !== this.props.activeFilters) {
      let filteredItems = this.filterCredentials(
        nextProps.credentials,
        nextProps.activeFilters
      );
      this.setState({ filteredItems: filteredItems });
    }
  }

  matchesFilter(item, filter) {
    let re = new RegExp(filter.value, 'i');

    switch (filter.field.id) {
      case 'name':
        return item.name.match(re) !== null;
      case 'credentialType':
        return item.cred_type === filter.value.id;
      case 'authenticationType':
        return item.auth_type === filter.value.id;
      default:
        return true;
    }
  }

  matchesFilters(item, filters) {
    let matches = true;

    filters.forEach(filter => {
      if (!this.matchesFilter(item, filter)) {
        matches = false;
        return false;
      }
    });
    return matches;
  }

  filterCredentials(credentials, filters) {
    if (!filters || filters.length === 0) {
      return credentials;
    }

    return credentials.filter(item => {
      return this.matchesFilters(item, filters);
    });
  }

  sortCredentials(items) {
    const { sortType, sortAscending } = this.props;

    let sortId = sortType ? sortType.id : 'name';

    items.sort((item1, item2) => {
      let compValue;
      switch (sortId) {
        case 'name':
          compValue = item1.name.localeCompare(item2.name);
          break;
        case 'credentialType':
          compValue = item1.cred_type.localeCompare(item2.cred_type);
          break;
        case 'authenticationType':
          compValue = item1.auth_type.localeCompare(item2.auth_type);
          break;
        default:
          compValue = 0;
      }

      if (!sortAscending) {
        compValue = compValue * -1;
      }

      return compValue;
    });
  }

  addCredential(credentialType) {
    Store.dispatch({
      type: credentialsTypes.CREATE_CREDENTIAL_SHOW,
      newCredentialType: credentialType
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
    const { filteredItems } = this.state;

    item.selected = !item.selected;
    let selectedItems = filteredItems.filter(item => {
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

  renderList(items) {
    return (
      <Row>
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
      </Row>
    );
  }

  render() {
    const { getPending, getError, getErrorMessage, credentials } = this.props;
    const { filteredItems, selectedItems } = this.state;

    if (getPending) {
      return (
        <Modal bsSize="lg" backdrop={false} show animation={false}>
          <Modal.Body>
            <div className="spinner spinner-xl" />
            <div className="text-center">Loading credentials...</div>
          </Modal.Body>
        </Modal>
      );
    }

    if (getError) {
      return (
        <EmptyState>
          <Alert type="error">
            <span>Error retrieving credentials: {getErrorMessage}</span>
          </Alert>
        </EmptyState>
      );
    }

    if (credentials && credentials.length) {
      this.sortCredentials(filteredItems);

      return (
        <React.Fragment>
          <div className="quipucords-view-container">
            <CredentialsToolbar
              totalCount={credentials.length}
              filteredCount={filteredItems.length}
              onAddCredential={this.addCredential}
              deleteAvailable={selectedItems && selectedItems.length > 0}
              onDelete={this.deleteCredentials}
              onRefresh={this.refresh}
            />
            <Grid fluid className="quipucords-list-container">
              {this.renderList(filteredItems)}
            </Grid>
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
  getPending: PropTypes.bool,
  credentials: PropTypes.array,
  getError: PropTypes.bool,
  getErrorMessage: PropTypes.string,

  activeFilters: PropTypes.array,
  sortType: PropTypes.object,
  sortAscending: PropTypes.bool
};

Credentials.defaultProps = {
  getPending: true
};

const mapDispatchToProps = (dispatch, ownProps) => ({
  getCredentials: () => dispatch(getCredentials())
});

const mapStateToProps = function(state) {
  return Object.assign({}, state.credentials, state.credentialsToolbar);
};

export default connect(mapStateToProps, mapDispatchToProps)(Credentials);
