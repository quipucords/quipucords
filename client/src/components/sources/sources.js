import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import { connect } from 'react-redux';

import { Alert, Button, EmptyState, Icon, ListView, Modal } from 'patternfly-react';

import { getSources } from '../../redux/actions/sourcesActions';
import { addScan } from '../../redux/actions/scansActions';
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
import { CreateScanDialog } from './createScanDialog';
import AddSourceWizard from '../addSourceWizard/addSourceWizard';
import { SourceFilterFields, SourceSortFields } from './sourceConstants';

class Sources extends React.Component {
  constructor() {
    super();

    helpers.bindMethods(this, [
      'scanSource',
      'scanSources',
      'itemSelectChange',
      'editSource',
      'deleteSource',
      'hideScanDialog',
      'createScan',
      'refresh',
      'showAddSourceWizard'
    ]);

    this.state = {
      scanDialogShown: false,
      multiSourceScan: false,
      currentScanSource: null,
      addSourceWizardShown: false
    };
  }

  componentDidMount() {
    this.props.getSources(helpers.createViewQueryObject(this.props.viewOptions));
  }

  componentWillReceiveProps(nextProps) {
    // Check for changes resulting in a fetch
    if (helpers.viewPropsChanged(nextProps.viewOptions, this.props.viewOptions)) {
      this.props.getSources(helpers.createViewQueryObject(nextProps.viewOptions));
    }
  }

  notifyCreateScanStatus(error, results) {
    if (error) {
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
            Started new scan <strong>{_.get(results, 'data.name')}</strong>.
          </span>
        )
      });
      this.hideScanDialog();
      this.props.getSources(helpers.createViewQueryObject(this.props.viewOptions));
    }
  }

  itemSelected(item) {
    const { selectedSources } = this.props;
    return (
      selectedSources.find(nextSelected => {
        return nextSelected.id === _.get(item, 'id');
      }) !== undefined
    );
  }

  showAddSourceWizard() {
    Store.dispatch({
      type: sourcesTypes.CREATE_SOURCE_SHOW
    });
  }

  editSource(item) {
    Store.dispatch({
      type: sourcesTypes.EDIT_SOURCE_SHOW,
      source: item
    });
  }

  scanSource(source) {
    this.setState({
      scanDialogShown: true,
      multiSourceScan: false,
      currentScanSource: source
    });
  }

  scanSources() {
    this.setState({ scanDialogShown: true, multiSourceScan: true });
  }

  hideScanDialog() {
    this.setState({ scanDialogShown: false });
  }

  itemSelectChange(item) {
    Store.dispatch({
      type: this.itemSelected(item) ? sourcesTypes.DESELECT_SOURCE : sourcesTypes.SELECT_SOURCE,
      source: item
    });
  }

  doDeleteSource(item) {
    Store.dispatch({
      type: confirmationModalTypes.CONFIRMATION_MODAL_HIDE
    });

    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: item.name,
      message: 'Deleting sources is not yet implemented'
    });
  }

  deleteSource(item) {
    let heading = (
      <span>
        Are you sure you want to delete the source <strong>{item.name}</strong>?
      </span>
    );

    let onConfirm = () => this.doDeleteSource(item);

    Store.dispatch({
      type: confirmationModalTypes.CONFIRMATION_MODAL_SHOW,
      title: 'Delete Source',
      heading: heading,
      confirmButtonText: 'Delete',
      onConfirm: onConfirm
    });
  }

  createScan(scanName, sources) {
    const { addScan } = this.props;

    let data = {
      name: scanName,
      sources: sources.map(item => item.id)
    };

    addScan(data).then(
      response => this.notifyCreateScanStatus(false, response.value),
      error => this.notifyCreateScanStatus(true, error.message)
    );
  }

  refresh() {
    this.props.getSources();
  }

  clearFilters() {
    Store.dispatch({
      type: viewToolbarTypes.CLEAR_FILTERS,
      viewType: viewTypes.SOURCES_VIEW
    });
  }

  renderSourceActions() {
    const { selectedSources } = this.props;

    return (
      <div className="form-group">
        <Button bsStyle="primary" onClick={this.showAddSourceWizard}>
          Add
        </Button>
        <Button disabled={!selectedSources || selectedSources.length === 0} onClick={this.scanSources}>
          Scan
        </Button>
        <Button onClick={this.refresh} bsStyle="success">
          <Icon type="fa" name="refresh" />
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
    if (_.size(items)) {
      return (
        <ListView className="quipicords-list-view">
          {items.map((item, index) => (
            <SourceListItem
              item={item}
              selected={this.itemSelected(item)}
              key={index}
              onItemSelectChange={this.itemSelectChange}
              onEdit={this.editSource}
              onDelete={this.deleteSource}
              onScan={this.scanSource}
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
          <Button bsStyle="link" onClick={this.clearFilters}>
            Clear Filters
          </Button>
        </EmptyState.Action>
      </EmptyState>
    );
  }

  render() {
    const { error, errorMessage, sources, selectedSources, viewOptions } = this.props;
    const { scanDialogShown, multiSourceScan, currentScanSource, addSourceWizardShown } = this.state;

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
              actions={this.renderSourceActions()}
              itemsType="Source"
              itemsTypePlural="Sources"
              selectedCount={selectedSources.length}
              {...viewOptions}
            />
            <ViewPaginationRow viewType={viewTypes.SOURCES_VIEW} {...viewOptions} />
            <div className="quipucords-list-container">{this.renderSourcesList(sources)}</div>
          </div>
          {this.renderPendingMessage()}
          <AddSourceWizard show={addSourceWizardShown} />
          <CreateScanDialog
            show={scanDialogShown}
            sources={multiSourceScan ? selectedSources : [currentScanSource]}
            onCancel={this.hideScanDialog}
            onScan={this.createScan}
          />
        </React.Fragment>
      );
    }

    return (
      <React.Fragment>
        <SourcesEmptyState onAddSource={this.showAddSourceWizard} />
        {this.renderPendingMessage()}
        <AddSourceWizard show={addSourceWizardShown} />
      </React.Fragment>
    );
  }
}

Sources.propTypes = {
  getSources: PropTypes.func,
  addScan: PropTypes.func,
  error: PropTypes.bool,
  errorMessage: PropTypes.string,
  pending: PropTypes.bool,
  sources: PropTypes.array,
  selectedSources: PropTypes.array,
  viewOptions: PropTypes.object
};

const mapDispatchToProps = (dispatch, ownProps) => ({
  getSources: queryObj => dispatch(getSources(queryObj)),
  addScan: data => dispatch(addScan(data))
});

const mapStateToProps = function(state) {
  return Object.assign({}, state.sources.view, state.sources.persist, {
    viewOptions: state.viewOptions[viewTypes.SOURCES_VIEW]
  });
};

export default connect(mapStateToProps, mapDispatchToProps)(Sources);
