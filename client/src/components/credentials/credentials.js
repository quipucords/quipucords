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
import Store from '../../redux/store';
import {
  confirmationModalTypes,
  credentialsTypes,
  toastNotificationTypes,
  viewTypes
} from '../../redux/constants';
import { bindMethods } from '../../common/helpers';

import ViewToolbar from '../viewToolbar/viewToolbar';
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
        } else {
          credential.auth_type = 'usernamePassword';
        }

        // TODO: Remove once we get real source data
        let sourceCount = Math.floor(Math.random() * 10);
        credential.sources = [];
        for (let i = 0; i < sourceCount; i++) {
          credential.sources.push('Source ' + (i + 1));
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

  matchString(value, match) {
    if (!value) {
      return false;
    }

    if (!match) {
      return true;
    }

    return value.toLowerCase().includes(match.toLowerCase());
  }

  matchesFilter(item, filter) {
    switch (filter.field.id) {
      case 'name':
        return this.matchString(item.name, filter.value);
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
      filterType,
      filterValue,
      activeFilters,
      sortType,
      sortAscending
    } = this.props;
    const { filteredItems } = this.state;

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
      this.sortCredentials(filteredItems);

      return (
        <React.Fragment>
          <div className="quipucords-view-container">
            <ViewToolbar
              viewType={viewTypes.CREDENTIALS_VIEW}
              totalCount={credentials.length}
              filteredCount={filteredItems.length}
              filterFields={CredentialFilterFields}
              sortFields={CredentialSortFields}
              actions={this.renderActions()}
              itemsType="Credential"
              itemsTypePlural="Credentials"
              filterType={filterType}
              filterValue={filterValue}
              activeFilters={activeFilters}
              sortType={sortType}
              sortAscending={sortAscending}
            />
            <div className="quipucords-list-container">
              {this.renderList(filteredItems)}
            </div>
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

  filterType: PropTypes.object,
  filterValue: PropTypes.oneOfType([PropTypes.string, PropTypes.object]),
  activeFilters: PropTypes.array,
  sortType: PropTypes.object,
  sortAscending: PropTypes.bool
};

const mapDispatchToProps = (dispatch, ownProps) => ({
  getCredentials: () => dispatch(getCredentials())
});

const mapStateToProps = function(state) {
  return Object.assign(
    {},
    state.credentials.view,
    state.credentials.persist,
    state.toolbars[viewTypes.CREDENTIALS_VIEW]
  );
};

export default connect(mapStateToProps, mapDispatchToProps)(Credentials);
