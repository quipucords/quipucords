import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { Alert, Button, DropdownButton, EmptyState, Form, Grid, ListView, MenuItem, Modal } from 'patternfly-react';
import _ from 'lodash';
import { reduxActions } from '../../redux/actions';
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

    this.credentialsToDelete = [];
    this.deletingCredential = null;

    this.state = {
      lastRefresh: null
    };
  }

  componentDidMount() {
    this.onRefresh();
  }

  componentWillReceiveProps(nextProps) {
    const { credentials, fulfilled, update, viewOptions } = this.props;

    if (!_.isEqual(nextProps.credentials, credentials) && nextProps.fulfilled && !fulfilled) {
      this.setState({ lastRefresh: Date.now() });
    }

    // Check for changes resulting in a fetch
    if (helpers.viewPropsChanged(nextProps.viewOptions, viewOptions)) {
      this.onRefresh(nextProps);
    }

    if (_.get(nextProps, 'update.delete')) {
      if (nextProps.update.fulfilled && !update.fulfilled) {
        Store.dispatch({
          type: toastNotificationTypes.TOAST_ADD,
          alertType: 'success',
          message: (
            <span>
              Credential <strong>{this.deletingCredential.name}</strong> successfully deleted.
            </span>
          )
        });
        this.onRefresh(nextProps);

        Store.dispatch({
          type: viewTypes.DESELECT_ITEM,
          viewType: viewTypes.CREDENTIALS_VIEW,
          item: this.deletingCredential
        });

        this.deleteNextCredential();
      }

      if (nextProps.update.error && !update.error) {
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

  onAddCredential = credentialType => {
    Store.dispatch({
      type: credentialsTypes.CREATE_CREDENTIAL_SHOW,
      credentialType
    });
  };

  onDeleteCredentials = () => {
    const { viewOptions } = this.props;

    if (viewOptions.selectedItems.length === 1) {
      this.onDeleteCredential(viewOptions.selectedItems[0]);
      return;
    }

    const heading = <span>Are you sure you want to delete the following credentials?</span>;

    let credentialsList = '';
    viewOptions.selectedItems.forEach((item, index) => {
      credentialsList += (index > 0 ? '\n' : '') + item.name;
    });

    const body = (
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

    const onConfirm = () => this.doDeleteCredentials(viewOptions.selectedItems);

    Store.dispatch({
      type: confirmationModalTypes.CONFIRMATION_MODAL_SHOW,
      title: 'Delete Credentials',
      heading,
      body,
      confirmButtonText: 'Delete',
      onConfirm
    });
  };

  onEditCredential = item => {
    Store.dispatch({
      type: credentialsTypes.EDIT_CREDENTIAL_SHOW,
      credential: item
    });
  };

  onDeleteCredential = item => {
    const heading = (
      <span>
        Are you sure you want to delete the credential <strong>{item.name}</strong>?
      </span>
    );

    const onConfirm = () => this.doDeleteCredentials([item]);

    Store.dispatch({
      type: confirmationModalTypes.CONFIRMATION_MODAL_SHOW,
      title: 'Delete Credential',
      heading,
      confirmButtonText: 'Delete',
      onConfirm
    });
  };

  onAddSource = () => {
    Store.dispatch({
      type: sourcesTypes.CREATE_SOURCE_SHOW
    });
  };

  onRefresh = props => {
    const { getCredentials, viewOptions } = this.props;
    const options = _.get(props, 'viewOptions') || viewOptions;

    getCredentials(helpers.createViewQueryObject(options));
  };

  onClearFilters = () => {
    Store.dispatch({
      type: viewToolbarTypes.CLEAR_FILTERS,
      viewType: viewTypes.CREDENTIALS_VIEW
    });
  };

  deleteNextCredential() {
    const { deleteCredential } = this.props;

    if (this.credentialsToDelete.length > 0) {
      this.deletingCredential = this.credentialsToDelete.pop();
      if (this.deletingCredential) {
        deleteCredential(this.deletingCredential.id);
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

  renderCredentialActions() {
    const { viewOptions } = this.props;

    return (
      <div className="form-group">
        <DropdownButton bsStyle="primary" title="Add" pullRight id="createCredentialButton">
          <MenuItem eventKey="1" onClick={() => this.onAddCredential('network')}>
            Network Credential
          </MenuItem>
          <MenuItem eventKey="2" onClick={() => this.onAddCredential('satellite')}>
            Satellite Credential
          </MenuItem>
          <MenuItem eventKey="2" onClick={() => this.onAddCredential('vcenter')}>
            VCenter Credential
          </MenuItem>
        </DropdownButton>
        <Button
          disabled={!viewOptions.selectedItems || viewOptions.selectedItems.length === 0}
          onClick={this.onDeleteCredentials}
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
          {items.map(item => (
            <CredentialListItem
              item={item}
              key={item.id}
              onEdit={this.onEditCredential}
              onDelete={this.onDeleteCredential}
            />
          ))}
        </ListView>
      );
    }

    return (
      <EmptyState className="list-view-blank-slate">
        <EmptyState.Title>No Results Match the Filter Criteria</EmptyState.Title>
        <EmptyState.Info>The active filters are hiding all items.</EmptyState.Info>
        <EmptyState.Action>
          <Button bsStyle="link" onClick={this.onClearFilters}>
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
              onRefresh={this.onRefresh}
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
        <CredentialsEmptyState onAddCredential={this.onAddCredential} onAddSource={this.onAddSource} />,
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

Credentials.defaultProps = {
  getCredentials: helpers.noop,
  deleteCredential: helpers.noop,
  fulfilled: false,
  error: false,
  errorMessage: null,
  pending: false,
  credentials: [],
  viewOptions: {},
  update: {}
};

const mapDispatchToProps = dispatch => ({
  getCredentials: queryObj => dispatch(reduxActions.credentials.getCredentials(queryObj)),
  deleteCredential: id => dispatch(reduxActions.credentials.deleteCredential(id))
});

const mapStateToProps = state =>
  Object.assign({}, state.credentials.view, {
    viewOptions: state.viewOptions[viewTypes.CREDENTIALS_VIEW],
    update: state.credentials.update
  });

const ConnectedCredentials = connect(
  mapStateToProps,
  mapDispatchToProps
)(Credentials);

export { ConnectedCredentials as default, ConnectedCredentials, Credentials };
