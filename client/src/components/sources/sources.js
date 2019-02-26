import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { Alert, Button, EmptyState, ListView, Modal } from 'patternfly-react';
import _ from 'lodash';
import { reduxActions } from '../../redux/actions';
import {
  sourcesTypes,
  toastNotificationTypes,
  confirmationModalTypes,
  viewTypes,
  viewToolbarTypes
} from '../../redux/constants';
import Store from '../../redux/store';
import helpers from '../../common/helpers';
import ViewToolbar from '../viewToolbar/viewToolbar';
import ViewPaginationRow from '../viewPaginationRow/viewPaginationRow';
import SourcesEmptyState from './sourcesEmptyState';
import SourceListItem from './sourceListItem';
import CreateScanDialog from './createScanDialog';
import { SourceFilterFields, SourceSortFields } from './sourceConstants';

class Sources extends React.Component {
  static notifyDeleteStatus(item, error, results) {
    try {
      if (error) {
        Store.dispatch({
          type: toastNotificationTypes.TOAST_ADD,
          alertType: 'error',
          header: 'Error',
          message: helpers.getMessageFromResults(results).message
        });
      } else {
        Store.dispatch({
          type: toastNotificationTypes.TOAST_ADD,
          alertType: 'success',
          message: (
            <span>
              Deleted source <strong>{_.get(item, 'name')}</strong>.
            </span>
          )
        });

        Store.dispatch({
          type: viewTypes.DESELECT_ITEM,
          viewType: viewTypes.SOURCES_VIEW,
          item
        });
      }
    } catch (e) {
      console.warn(e);
    }
  }

  constructor() {
    super();

    this.state = {
      scanDialogShown: false,
      multiSourceScan: false,
      currentScanSource: null,
      lastRefresh: null
    };
  }

  componentDidMount() {
    this.onRefresh();
  }

  componentWillReceiveProps(nextProps) {
    const { viewOptions, updateSources, deleted, fulfilled } = this.props;

    // Check for changes resulting in a fetch
    if (helpers.viewPropsChanged(nextProps.viewOptions, viewOptions)) {
      this.onRefresh(nextProps);
    }

    if ((nextProps.updateSources && !updateSources) || (nextProps.deleted && !deleted)) {
      this.onRefresh();
    }

    if (nextProps.fulfilled && !fulfilled) {
      this.setState({ lastRefresh: Date.now() });
    }
  }

  onShowAddSourceWizard = () => {
    Store.dispatch({
      type: sourcesTypes.CREATE_SOURCE_SHOW
    });
  };

  onEditSource = item => {
    Store.dispatch({
      type: sourcesTypes.EDIT_SOURCE_SHOW,
      source: item
    });
  };

  onScanSource = source => {
    this.setState({
      scanDialogShown: true,
      multiSourceScan: false,
      currentScanSource: source
    });
  };

  onScanSources = () => {
    this.setState({ scanDialogShown: true, multiSourceScan: true });
  };

  onHideScanDialog = updated => {
    this.setState({ scanDialogShown: false });

    if (updated) {
      this.onRefresh();
    }
  };

  onHandleDeleteSource = item => {
    const heading = (
      <span>
        Are you sure you want to delete the source <strong>{item.name}</strong>?
      </span>
    );

    const onConfirm = () => this.doDeleteSource(item);

    Store.dispatch({
      type: confirmationModalTypes.CONFIRMATION_MODAL_SHOW,
      title: 'Delete Source',
      heading,
      confirmButtonText: 'Delete',
      onConfirm
    });
  };

  onRefresh = props => {
    const { getSources, viewOptions } = this.props;
    const options = _.get(props, 'viewOptions') || viewOptions;

    getSources(helpers.createViewQueryObject(options));
  };

  onClearFilters = () => {
    Store.dispatch({
      type: viewToolbarTypes.CLEAR_FILTERS,
      viewType: viewTypes.SOURCES_VIEW
    });
  };

  doDeleteSource(item) {
    const { deleteSource } = this.props;

    Store.dispatch({
      type: confirmationModalTypes.CONFIRMATION_MODAL_HIDE
    });

    deleteSource(item.id).then(
      response => Sources.notifyDeleteStatus(item, false, response.value),
      error => Sources.notifyDeleteStatus(item, true, error)
    );
  }

  renderSourceActions() {
    const { viewOptions } = this.props;

    return (
      <div className="form-group">
        <Button bsStyle="primary" onClick={this.onShowAddSourceWizard}>
          Add
        </Button>
        <Button
          disabled={!viewOptions.selectedItems || viewOptions.selectedItems.length === 0}
          onClick={this.onScanSources}
        >
          Scan
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
            <div className="text-center">Loading sources...</div>
          </Modal.Body>
        </Modal>
      );
    }

    return null;
  }

  renderSourcesList(items) {
    const { lastRefresh } = this.state;

    if (_.size(items)) {
      return (
        <ListView className="quipicords-list-view">
          {items.map(item => (
            <SourceListItem
              item={item}
              key={item.id}
              lastRefresh={lastRefresh}
              onEdit={this.onEditSource}
              onDelete={this.onHandleDeleteSource}
              onScan={this.onScanSource}
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
    const { error, errorMessage, sources, viewOptions } = this.props;
    const { scanDialogShown, multiSourceScan, currentScanSource, lastRefresh } = this.state;

    if (error) {
      return (
        <EmptyState>
          <Alert type="error">
            <span>Error retrieving sources: {errorMessage}</span>
          </Alert>
          {this.renderPendingMessage()}
        </EmptyState>
      );
    }

    if (_.size(sources) || _.size(viewOptions.activeFilters)) {
      return (
        <React.Fragment>
          <div className="quipucords-view-container">
            <ViewToolbar
              viewType={viewTypes.SOURCES_VIEW}
              filterFields={SourceFilterFields}
              sortFields={SourceSortFields}
              onRefresh={this.onRefresh}
              lastRefresh={lastRefresh}
              actions={this.renderSourceActions()}
              itemsType="Source"
              itemsTypePlural="Sources"
              selectedCount={viewOptions.selectedItems.length}
              {...viewOptions}
            />
            <ViewPaginationRow viewType={viewTypes.SOURCES_VIEW} {...viewOptions} />
            <div className="quipucords-list-container">{this.renderSourcesList(sources)}</div>
          </div>
          {this.renderPendingMessage()}
          <CreateScanDialog
            show={scanDialogShown}
            sources={multiSourceScan ? viewOptions.selectedItems : [currentScanSource]}
            onClose={this.onHideScanDialog}
          />
        </React.Fragment>
      );
    }

    return (
      <React.Fragment>
        <SourcesEmptyState onAddSource={this.onShowAddSourceWizard} />
        {this.renderPendingMessage()}
      </React.Fragment>
    );
  }
}

Sources.propTypes = {
  getSources: PropTypes.func,
  deleteSource: PropTypes.func,
  error: PropTypes.bool,
  errorMessage: PropTypes.string,
  pending: PropTypes.bool,
  sources: PropTypes.array,
  lastRefresh: PropTypes.object,
  viewOptions: PropTypes.object,
  fulfilled: PropTypes.bool,
  updateSources: PropTypes.bool,
  deleted: PropTypes.bool
};

Sources.defaultProps = {
  getSources: helpers.noop,
  deleteSource: helpers.noop,
  error: false,
  errorMessage: null,
  pending: false,
  sources: [],
  lastRefresh: {},
  viewOptions: {},
  fulfilled: false,
  updateSources: false,
  deleted: false
};

const mapDispatchToProps = dispatch => ({
  getSources: queryObj => dispatch(reduxActions.sources.getSources(queryObj)),
  deleteSource: id => dispatch(reduxActions.sources.deleteSource(id))
});

const mapStateToProps = state =>
  Object.assign(
    {},
    state.sources.view,
    { viewOptions: state.viewOptions[viewTypes.SOURCES_VIEW] },
    { deleted: state.sources.update.fulfilled }
  );

const ConnectedSources = connect(
  mapStateToProps,
  mapDispatchToProps
)(Sources);

export { ConnectedSources as default, ConnectedSources, Sources };
