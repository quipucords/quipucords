import PropTypes from 'prop-types';
import React from 'react';
import { connect } from 'react-redux';

import {
  Alert,
  Grid,
  EmptyState,
  Row,
  ListView,
  Modal
} from 'patternfly-react';

import { getCredentials } from '../../redux/actions/credentialsActions';

import CredentialsToolbar from './credentialsToolbar';
import CredentialsEmptyState from './credentialsEmptyState';
import { CredentialListItem } from './credentialListItem';
import Store from '../../redux/store';
import { toastNotificationTypes } from '../../redux/constants';
import { bindMethods } from '../../common/helpers';

class Credentials extends React.Component {
  constructor() {
    super();

    bindMethods(this, [
      'addCredential',
      'deleteCredentials',
      'itemSelectChange',
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

  addCredential() {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: 'NYI',
      message: 'Adding credentials is not yet implemented'
    });
  }

  deleteCredentials() {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: 'NYI',
      message: 'Deleting credentials is not yet implemented'
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
            />
          ))}
        </ListView>
      </Row>
    );
  }

  render() {
    const { loading, loadError, errorMessage, credentials } = this.props;
    const { filteredItems, selectedItems } = this.state;

    if (loading) {
      return (
        <Modal bsSize="lg" backdrop={false} show animation={false}>
          <Modal.Body>
            <div className="spinner spinner-xl" />
            <div className="text-center">Loading credentials...</div>
          </Modal.Body>
        </Modal>
      );
    }
    if (loadError) {
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

      return [
        <CredentialsToolbar
          totalCount={credentials.length}
          filteredCount={filteredItems.length}
          key={1}
          onAddCredential={this.addCredential}
          deleteAvailable={selectedItems && selectedItems.length > 0}
          onDelete={this.deleteCredentials}
          onRefresh={this.refresh}
        />,
        <Grid fluid key={2}>
          {this.renderList(filteredItems)}
        </Grid>
      ];
    }
    return (
      <CredentialsEmptyState
        onAddCredential={this.addCredential}
        onAddSource={this.addSource}
        onImportSources={this.importSources}
      />
    );
  }
}

Credentials.propTypes = {
  getCredentials: PropTypes.func,
  loadError: PropTypes.bool,
  errorMessage: PropTypes.string,
  loading: PropTypes.bool,
  credentials: PropTypes.array,
  activeFilters: PropTypes.array,
  sortType: PropTypes.object,
  sortAscending: PropTypes.bool
};

Credentials.defaultProps = {
  loading: true
};

const mapDispatchToProps = (dispatch, ownProps) => ({
  getCredentials: () => dispatch(getCredentials())
});

function mapStateToProps(state) {
  return {
    loading: state.credentials.loading,
    credentials: state.credentials.data,
    loadError: state.credentials.error,
    errorMessage: state.credentials.errorMessage,
    activeFilters: state.credentialsToolbar.activeFilters,
    sortType: state.credentialsToolbar.sortType,
    sortAscending: state.credentialsToolbar.sortAscending
  };
}

export default connect(mapStateToProps, mapDispatchToProps)(Credentials);
