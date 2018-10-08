import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import { connect } from 'react-redux';

import { Alert, Button, DropdownButton, EmptyState, Form, Grid, ListView, MenuItem, Modal } from 'patternfly-react';

import { getCredentials, deleteCredential } from '../../redux/actions/credentialsActions';
import {
  confirmationModalTypes,
  credentialsTypes,
  sourcesTypes,
  toastNotificationTypes,
  viewToolbarTypes,
  viewTypes
} from '../../redux/constants';
import Store from '../../redux/store';
import helpers from '../../common/helpers';

import ViewToolbar from '../viewToolbar/viewToolbar';
import ViewPaginationRow from '../viewPaginationRow/viewPaginationRow';

import CredentialsEmptyState from './credentialsEmptyState';
import CredentialListItem from './credentialListItem';
import { CredentialFilterFields, CredentialSortFields } from './crendentialConstants';

class Credentials extends React.Component {
  constructor() {
    super();

    helpers.bindMethods(this, [
      'addCredential',
      'deleteCredentials',
      'editCredential',
      'deleteCredential',
      'addSource',
      'refresh'
    ]);

    this.credentialsToDelete = [];
    this.deletingCredential = null;

    this.state = {
      lastRefresh: null
    };
  }

  componentDidMount() {
    this.refresh();
  }

  componentWillReceiveProps(nextProps) {
    if (!_.isEqual(nextProps.credentials, this.props.credentials)) {
      // Reset selection state though we may want to keep selections over refreshes...
      nextProps.credentials.forEach(credential => {
        if (credential.ssh_keyfile && credential.ssh_keyfile !== '') {
          credential.auth_type = 'sshKey';
        } else {
          credential.auth_type = 'usernamePassword';
        }
      });

      if (nextProps.fulfilled && !this.props.fulfilled) {
        this.setState({ lastRefresh: Date.now() });
      }
    }

    // Check for changes resulting in a fetch
    if (helpers.viewPropsChanged(nextProps.viewOptions, this.props.viewOptions)) {
      this.refresh(nextProps);
    }

    if (_.get(nextProps, 'update.delete')) {
      if (nextProps.update.fulfilled && !this.props.update.fulfilled) {
        Store.dispatch({
          type: toastNotificationTypes.TOAST_ADD,
          alertType: 'success',
          message: (
            <span>
              Credential <strong>{this.deletingCredential.name}</strong> successfully deleted.
            </span>
          )
        });
        this.refresh(nextProps);

        Store.dispatch({
          type: viewTypes.DESELECT_ITEM,
          viewType: viewTypes.CREDENTIALS_VIEW,
          item: this.deletingCredential
        });

        this.deleteNextCredential();
      }

      if (nextProps.update.error && !this.props.update.error) {
        Store.dispatch({
          type: toastNotificationTypes.TOAST_ADD,
          alertType: 'error',
          header: 'Error',
          message: (
            <span>
              Error removing credential <strong>{this.deletingCredential.name}</strong>
              <p>{nextProps.update.errorMessage}</p>
            </span>
          )
        });

        this.deleteNextCredential();
      }
    }
  }

  addCredential(credentialType) {
    Store.dispatch({
      type: credentialsTypes.CREATE_CREDENTIAL_SHOW,
      credentialType
    });
  }

  deleteNextCredential() {
    if (this.credentialsToDelete.length > 0) {
      this.deletingCredential = this.credentialsToDelete.pop();
      if (this.deletingCredential) {
        this.props.deleteCredential(this.deletingCredential.id);
      }
    }
  }

  doDeleteCredentials(items) {
    this.credentialsToDelete = [...items];

    Store.dispatch({
      type: confirmationModalTypes.CONFIRMATION_MODAL_HIDE
    });

    this.deleteNextCredential();
  }

  deleteCredentials() {
    const { viewOptions } = this.props;

    if (viewOptions.selectedItems.length === 1) {
      this.deleteCredential(viewOptions.selectedItems[0]);
      return;
    }

    let heading = <span>Are you sure you want to delete the following credentials?</span>;

    let credentialsList = '';
    viewOptions.selectedItems.forEach((item, index) => {
      return (credentialsList += (index > 0 ? '\n' : '') + item.name);
    });

    let body = (
      <Grid.Col sm={12}>
        <Form.FormControl
          className="quipucords-form-control"
          componentClass="textarea"
          type="textarea"
          readOnly
          rows={viewOptions.selectedItems.length}
          value={credentialsList}
        />
      </Grid.Col>
    );

    let onConfirm = () => this.doDeleteCredentials(viewOptions.selectedItems);

    Store.dispatch({
      type: confirmationModalTypes.CONFIRMATION_MODAL_SHOW,
      title: 'Delete Credentials',
      heading: heading,
      body: body,
      confirmButtonText: 'Delete',
      onConfirm: onConfirm
    });
  }

  editCredential(item) {
    Store.dispatch({
      type: credentialsTypes.EDIT_CREDENTIAL_SHOW,
      credential: item
    });
  }

  deleteCredential(item) {
    let heading = (
      <span>
        Are you sure you want to delete the credential <strong>{item.name}</strong>?
      </span>
    );

    let onConfirm = () => this.doDeleteCredentials([item]);

    Store.dispatch({
      type: confirmationModalTypes.CONFIRMATION_MODAL_SHOW,
      title: 'Delete Credential',
      heading: heading,
      confirmButtonText: 'Delete',
      onConfirm: onConfirm
    });
  }

  addSource() {
    Store.dispatch({
      type: sourcesTypes.CREATE_SOURCE_SHOW
    });
  }

  refresh(props) {
    const options = _.get(props, 'viewOptions') || this.props.viewOptions;
    this.props.getCredentials(helpers.createViewQueryObject(options));
  }

  clearFilters() {
    Store.dispatch({
      type: viewToolbarTypes.CLEAR_FILTERS,
      viewType: viewTypes.CREDENTIALS_VIEW
    });
  }

  renderCredentialActions() {
    const { viewOptions } = this.props;

    return (
      <div className="form-group">
        <DropdownButton bsStyle="primary" title="Add" pullRight id="createCredentialButton">
          <MenuItem eventKey="1" onClick={() => this.addCredential('network')}>
            Network Credential
          </MenuItem>
          <MenuItem eventKey="2" onClick={() => this.addCredential('satellite')}>
            Satellite Credential
          </MenuItem>
          <MenuItem eventKey="2" onClick={() => this.addCredential('vcenter')}>
            VCenter Credential
          </MenuItem>
        </DropdownButton>
        <Button
          disabled={!viewOptions.selectedItems || viewOptions.selectedItems.length === 0}
          onClick={this.deleteCredentials}
        >
          Delete
        </Button>
      </div>
    );
  }

  renderPendingMessage() {
    const { pending } = this.props;

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

    return null;
  }

  renderCredentialsList(items) {
    if (_.size(items)) {
      return (
        <ListView className="quipicords-list-view">
          {items.map((item, index) => (
            <CredentialListItem item={item} key={index} onEdit={this.editCredential} onDelete={this.deleteCredential} />
          ))}
        </ListView>
      );
    }

    return (
      <EmptyState className="list-view-blank-slate">
        <EmptyState.Title>No Results Match the Filter Criteria</EmptyState.Title>
        <EmptyState.Info>The active filters are hiding all items.</EmptyState.Info>
        <EmptyState.Action>
          <Button bsStyle="link" onClick={this.clearFilters}>
            Clear Filters
          </Button>
        </EmptyState.Action>
      </EmptyState>
    );
  }

  render() {
    const { error, errorMessage, credentials, viewOptions } = this.props;
    const { lastRefresh } = this.state;

    if (error) {
      return (
        <EmptyState>
          <Alert type="error">
            <span>Error retrieving credentials: {errorMessage}</span>
          </Alert>
          {this.renderPendingMessage()}
        </EmptyState>
      );
    }

    if (_.size(credentials) || _.size(viewOptions.activeFilters)) {
      return (
        <React.Fragment>
          <div className="quipucords-view-container">
            <ViewToolbar
              viewType={viewTypes.CREDENTIALS_VIEW}
              filterFields={CredentialFilterFields}
              sortFields={CredentialSortFields}
              onRefresh={this.refresh}
              lastRefresh={lastRefresh}
              actions={this.renderCredentialActions()}
              itemsType="Credential"
              itemsTypePlural="Credentials"
              selectedCount={viewOptions.selectedItems.length}
              {...viewOptions}
            />
            <ViewPaginationRow viewType={viewTypes.CREDENTIALS_VIEW} {...viewOptions} />
            <div className="quipucords-list-container">{this.renderCredentialsList(credentials)}</div>
          </div>
          {this.renderPendingMessage()}
        </React.Fragment>
      );
    }

    return (
      <React.Fragment>
        {this.renderPendingMessage()}
        <CredentialsEmptyState onAddCredential={this.addCredential} onAddSource={this.addSource} />,
      </React.Fragment>
    );
  }
}

Credentials.propTypes = {
  getCredentials: PropTypes.func,
  deleteCredential: PropTypes.func,
  fulfilled: PropTypes.bool,
  error: PropTypes.bool,
  errorMessage: PropTypes.string,
  pending: PropTypes.bool,
  credentials: PropTypes.array,
  viewOptions: PropTypes.object,
  update: PropTypes.object
};

const mapDispatchToProps = (dispatch, ownProps) => ({
  getCredentials: queryObj => dispatch(getCredentials(queryObj)),
  deleteCredential: id => dispatch(deleteCredential(id))
});

const mapStateToProps = function(state) {
  return Object.assign({}, state.credentials.view, {
    viewOptions: state.viewOptions[viewTypes.CREDENTIALS_VIEW],
    update: state.credentials.update
  });
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(Credentials);
