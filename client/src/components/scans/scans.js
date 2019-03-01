import React from 'react';
import PropTypes from 'prop-types';
import { Redirect } from 'react-router-dom';
import { Alert, Button, DropdownButton, EmptyState, Grid, Form, ListView, MenuItem, Modal } from 'patternfly-react';
import _ from 'lodash';
import { connect, reduxActions, reduxTypes, store } from '../../redux';
import helpers from '../../common/helpers';
import ViewToolbar from '../viewToolbar/viewToolbar';
import ViewPaginationRow from '../viewPaginationRow/viewPaginationRow';
import ScansEmptyState from './scansEmptyState';
import ScanListItem from './scanListItem';
import { ScanFilterFields, ScanSortFields } from './scanConstants';
import SimpleTooltip from '../simpleTooltIp/simpleTooltip';
import MergeReportsDialog from '../mergeReportsDialog/mergeReportsDialog';

class Scans extends React.Component {
  static notifyDownloadStatus(error, results) {
    if (error) {
      store.dispatch({
        type: reduxTypes.toastNotifications.TOAST_ADD,
        alertType: 'error',
        header: 'Error',
        message: helpers.getMessageFromResults(results).message
      });
    } else {
      store.dispatch({
        type: reduxTypes.toastNotifications.TOAST_ADD,
        alertType: 'success',
        message: <span>Report downloaded.</span>
      });
    }
  }

  /**
   * FixMe: Deletions of scans is not currently desired. This is here in case it ever gets added.
   * FUTURE: Delete is fully functional by setting okToDelete to true.
   */
  okToDelete = false;

  state = {
    scansToDelete: [],
    deletingScan: null,
    redirectTo: null
  };

  componentDidMount() {
    this.onRefresh();
  }

  componentDidUpdate(previousProps) {
    const { update, viewOptions } = this.props;
    const { deletingScan } = this.state;

    // Check for changes resulting in a fetch
    if (helpers.viewPropsChanged(previousProps.viewOptions, viewOptions)) {
      this.onRefresh();
    }

    if (_.get(update, 'delete')) {
      if (previousProps.update.fulfilled && !update.fulfilled) {
        store.dispatch({
          type: reduxTypes.toastNotifications.TOAST_ADD,
          alertType: 'success',
          message: (
            <span>
              Scan <strong>{deletingScan.name}</strong> successfully deleted.
            </span>
          )
        });

        this.onRefresh();

        store.dispatch({
          type: reduxTypes.view.DESELECT_ITEM,
          viewType: reduxTypes.view.SCANS_VIEW,
          item: deletingScan
        });

        this.deleteNextScan();
      }

      if (previousProps.update.error && !update.error) {
        store.dispatch({
          type: reduxTypes.toastNotifications.TOAST_ADD,
          alertType: 'error',
          header: 'Error',
          message: (
            <span>
              Error removing scan <strong>{deletingScan.name}</strong>
              <p>{update.errorMessage}</p>
            </span>
          )
        });

        this.deleteNextScan();
      }
    }
  }

  onDownloadSummaryReport = reportId => {
    const { getReportSummaryCsv } = this.props;

    getReportSummaryCsv(reportId).then(
      () => Scans.notifyDownloadStatus(false),
      error => Scans.notifyDownloadStatus(true, error.message)
    );
  };

  onDownloadDetailedReport = reportId => {
    const { getReportDetailsCsv } = this.props;

    getReportDetailsCsv(reportId).then(
      () => Scans.notifyDownloadStatus(false),
      error => Scans.notifyDownloadStatus(true, error.message)
    );
  };

  onMergeScanResults = details => {
    const { viewOptions } = this.props;

    store.dispatch({
      type: reduxTypes.scans.MERGE_SCAN_DIALOG_SHOW,
      show: true,
      scans: viewOptions.selectedItems,
      details
    });
  };

  onDoStartScan = item => {
    const { startScan } = this.props;

    startScan(item.id).then(
      response => this.notifyActionStatus(item, 'started', false, response.value),
      error => this.notifyActionStatus(item, 'started', true, error)
    );
  };

  onDoPauseScan = item => {
    const { pauseScan } = this.props;

    pauseScan(item.most_recent.id).then(
      response => this.notifyActionStatus(item, 'paused', false, response.value),
      error => this.notifyActionStatus(item, 'paused', true, error)
    );
  };

  onDoResumeScan = item => {
    const { restartScan } = this.props;

    restartScan(item.most_recent.id).then(
      response => this.notifyActionStatus(item, 'resumed', false, response.value),
      error => this.notifyActionStatus(item, 'resumed', true, error)
    );
  };

  onDoCancelScan = item => {
    const { cancelScan } = this.props;

    cancelScan(item.most_recent.id).then(
      response => this.notifyActionStatus(item, 'canceled', false, response.value),
      error => this.notifyActionStatus(item, 'canceled', true, error)
    );
  };

  onAddSource = () => {
    const { sourcesCount } = this.props;

    if (sourcesCount) {
      this.setState({ redirectTo: '/sources' });
    } else {
      store.dispatch({
        type: reduxTypes.sources.CREATE_SOURCE_SHOW
      });
    }
  };

  onRefresh = () => {
    const { getScans, getScansSources, viewOptions } = this.props;

    getScansSources();
    getScans(helpers.createViewQueryObject(viewOptions, { scan_type: 'inspect' }));
  };

  onDeleteScans = () => {
    const { viewOptions } = this.props;

    if (_.size(viewOptions.selectedItems) === 0) {
      return;
    }

    if (_.size(viewOptions.selectedItems) === 1) {
      this.handleDeleteScan(viewOptions.selectedItems[0]);
      return;
    }

    const heading = <span>Are you sure you want to delete the following scans?</span>;

    let scansList = '';
    viewOptions.selectedItems.forEach((item, index) => {
      scansList += (index > 0 ? '\n' : '') + item.name;
    });

    const body = (
      <Grid.Col sm={12}>
        <Form.FormControl
          className="quipucords-form-control"
          componentClass="textarea"
          type="textarea"
          readOnly
          rows={viewOptions.selectedItems.length}
          value={scansList}
        />
      </Grid.Col>
    );

    const onConfirm = () => this.doDeleteScans(viewOptions.selectedItems);

    store.dispatch({
      type: reduxTypes.confirmationModal.CONFIRMATION_MODAL_SHOW,
      title: 'Delete Scans',
      heading,
      body,
      confirmButtonText: 'Delete',
      onConfirm
    });
  };

  onClearFilters = () => {
    store.dispatch({
      type: reduxTypes.viewToolbar.CLEAR_FILTERS,
      viewType: reduxTypes.view.SCANS_VIEW
    });
  };

  notifyActionStatus(scan, actionText, error, results) {
    if (error) {
      store.dispatch({
        type: reduxTypes.toastNotifications.TOAST_ADD,
        alertType: 'error',
        header: 'Error',
        message: helpers.getMessageFromResults(results).message
      });
    } else {
      store.dispatch({
        type: reduxTypes.toastNotifications.TOAST_ADD,
        alertType: 'success',
        message: (
          <span>
            Scan <strong>{scan.name}</strong> {actionText}.
          </span>
        )
      });

      this.onRefresh();
    }
  }

  deleteNextScan() {
    const { deleteScan } = this.props;
    const { scansToDelete } = this.state;

    if (scansToDelete.length > 0) {
      const nextDeletingScan = scansToDelete.pop();

      this.setState(
        {
          deletingScan: nextDeletingScan
        },
        () => {
          if (nextDeletingScan) {
            deleteScan(nextDeletingScan.id);
          }
        }
      );
    }
  }

  doDeleteScans(items) {
    this.setState(
      {
        scansToDelete: [...items]
      },
      () => this.deleteNextScan()
    );

    store.dispatch({
      type: reduxTypes.confirmationModal.CONFIRMATION_MODAL_HIDE
    });
  }

  handleDeleteScan(item) {
    const heading = (
      <span>
        Are you sure you want to delete the scan <strong>{item.name}</strong>?
      </span>
    );

    const onConfirm = () => this.doDeleteScans([item]);

    store.dispatch({
      type: reduxTypes.confirmationModal.CONFIRMATION_MODAL_SHOW,
      title: 'Delete Scan',
      heading,
      confirmButtonText: 'Delete',
      onConfirm
    });
  }

  renderPendingMessage() {
    const { pending } = this.props;

    if (pending) {
      return (
        <Modal bsSize="lg" backdrop={false} show animation={false}>
          <Modal.Body>
            <div className="spinner spinner-xl" />
            <div className="text-center">Loading scans...</div>
          </Modal.Body>
        </Modal>
      );
    }

    return null;
  }

  renderScansActions() {
    const { viewOptions } = this.props;
    const mergeAllowed = _.size(viewOptions.selectedItems) > 1;

    // FUTURE: deletion is not currently enabled
    let deleteAction = null;
    if (this.okToDelete) {
      deleteAction = (
        <Button disabled={_.size(viewOptions.selectedItems) === 0} onClick={this.onDeleteScans}>
          Delete
        </Button>
      );
    }

    return (
      <div className="form-group">
        <SimpleTooltip
          key="mergeButtonTip"
          id="mergeButtonTip"
          tooltip="Merge selected scan results into a single report"
        >
          <DropdownButton key="mergeButton" title="Merge Report" id="merge-reports-dropdown" disabled={!mergeAllowed}>
            <MenuItem eventKey="1" onClick={() => this.onMergeScanResults(false)}>
              Summary Report
            </MenuItem>
            <MenuItem eventKey="2" onClick={() => this.onMergeScanResults(true)}>
              Detailed Report
            </MenuItem>
          </DropdownButton>
        </SimpleTooltip>
        {deleteAction}
      </div>
    );
  }

  renderScansList(items) {
    const { lastRefresh } = this.props;

    if (_.size(items)) {
      return (
        <ListView className="quipicords-list-view">
          {items.map(item => (
            <ScanListItem
              item={item}
              key={item.id}
              lastRefresh={lastRefresh}
              onSummaryDownload={this.onDownloadSummaryReport}
              onDetailedDownload={this.onDownloadDetailedReport}
              onStart={this.onDoStartScan}
              onPause={this.onDoPauseScan}
              onResume={this.onDoResumeScan}
              onCancel={this.onDoCancelScan}
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
    const { lastRefresh, error, errorMessage, scans, sourcesCount, viewOptions } = this.props;
    const { redirectTo } = this.state;

    if (error) {
      return (
        <EmptyState>
          <Alert type="error">
            <span>Error retrieving scans: {errorMessage}</span>
          </Alert>
          {this.renderPendingMessage()}
        </EmptyState>
      );
    }

    if (redirectTo) {
      return <Redirect to={redirectTo} push />;
    }

    if (_.size(scans) || _.size(viewOptions.activeFilters)) {
      return (
        <React.Fragment>
          <div className="quipucords-view-container">
            <ViewToolbar
              viewType={reduxTypes.view.SCANS_VIEW}
              filterFields={ScanFilterFields}
              sortFields={ScanSortFields}
              onRefresh={this.onRefresh}
              lastRefresh={lastRefresh}
              actions={this.renderScansActions()}
              itemsType="Scan"
              itemsTypePlural="Scans"
              selectedCount={viewOptions.selectedItems.length}
              {...viewOptions}
            />
            <ViewPaginationRow viewType={reduxTypes.view.SCANS_VIEW} {...viewOptions} />
            <div className="quipucords-list-container">{this.renderScansList(scans)}</div>
          </div>
          {this.renderPendingMessage()}
          <MergeReportsDialog />
        </React.Fragment>
      );
    }

    return (
      <React.Fragment>
        <ScansEmptyState onAddSource={this.onAddSource} sourcesExist={!!sourcesCount} />
        {this.renderPendingMessage()}
      </React.Fragment>
    );
  }
}

Scans.propTypes = {
  getScans: PropTypes.func,
  startScan: PropTypes.func,
  pauseScan: PropTypes.func,
  cancelScan: PropTypes.func,
  restartScan: PropTypes.func,
  deleteScan: PropTypes.func,
  getScansSources: PropTypes.func,
  getReportSummaryCsv: PropTypes.func,
  getReportDetailsCsv: PropTypes.func,
  fulfilled: PropTypes.bool,
  error: PropTypes.bool,
  errorMessage: PropTypes.string,
  pending: PropTypes.bool,
  scans: PropTypes.array,
  lastRefresh: PropTypes.number,
  sourcesCount: PropTypes.number,
  viewOptions: PropTypes.object,
  update: PropTypes.object
};

Scans.defaultProps = {
  getScans: helpers.noop,
  startScan: helpers.noop,
  pauseScan: helpers.noop,
  cancelScan: helpers.noop,
  restartScan: helpers.noop,
  deleteScan: helpers.noop,
  getScansSources: helpers.noop,
  getReportSummaryCsv: helpers.noop,
  getReportDetailsCsv: helpers.noop,
  fulfilled: false,
  error: false,
  errorMessage: null,
  pending: false,
  scans: [],
  lastRefresh: 0,
  sourcesCount: 0,
  viewOptions: {},
  update: {}
};

const mapDispatchToProps = dispatch => ({
  getScans: queryObj => dispatch(reduxActions.scans.getScans(queryObj)),
  startScan: id => dispatch(reduxActions.scans.startScan(id)),
  pauseScan: id => dispatch(reduxActions.scans.pauseScan(id)),
  restartScan: id => dispatch(reduxActions.scans.restartScan(id)),
  cancelScan: id => dispatch(reduxActions.scans.cancelScan(id)),
  deleteScan: id => dispatch(reduxActions.scans.deleteScan(id)),
  getScansSources: queryObj => dispatch(reduxActions.sources.getScansSources(queryObj)),
  getReportSummaryCsv: (id, query) => dispatch(reduxActions.reports.getReportSummaryCsv(id, query)),
  getReportDetailsCsv: id => dispatch(reduxActions.reports.getReportDetailsCsv(id))
});

const mapStateToProps = state =>
  Object.assign({}, state.scans.view, {
    viewOptions: state.viewOptions[reduxTypes.view.SCANS_VIEW],
    update: state.scans.update
  });

const ConnectedScans = connect(
  mapStateToProps,
  mapDispatchToProps
)(Scans);

export { ConnectedScans as default, ConnectedScans, Scans };
