import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import { connect } from 'react-redux';

import { Alert, Button, EmptyState, ListView, Modal } from 'patternfly-react';

import { getScans, startScan, pauseScan, cancelScan, restartScan } from '../../redux/actions/scansActions';
import { getReportDeploymentsCsv, getReportDetailsCsv } from '../../redux/actions/reportsActions';
import { sourcesTypes, toastNotificationTypes, viewToolbarTypes, viewTypes } from '../../redux/constants';
import Store from '../../redux/store';
import helpers from '../../common/helpers';

import ViewToolbar from '../viewToolbar/viewToolbar';
import ViewPaginationRow from '../viewPaginationRow/viewPaginationRow';

import SourcesEmptyState from '../sources/sourcesEmptyState';
import ScanListItem from './scanListItem';
import { ScanFilterFields, ScanSortFields } from './scanConstants';

class Scans extends React.Component {
  constructor() {
    super();

    helpers.bindMethods(this, [
      'doUpdate',
      'downloadSummaryReport',
      'downloadDetailedReport',
      'doPauseScan',
      'doCancelScan',
      'doStartScan',
      'doResumeScan',
      'addSource',
      'refresh',
      'notifyActionStatus'
    ]);

    this.state = {
      lastRefresh: null
    };

    this.pollingInterval = null;
    this.mounted = false;
  }

  componentDidMount() {
    this.props.getScans(
      helpers.createViewQueryObject(this.props.viewOptions, {
        scan_type: 'inspect'
      })
    );
    this.mounted = true;
  }

  componentWillUnmount() {
    this.stopPolling();
    this.mounted = false;
  }

  componentWillReceiveProps(nextProps) {
    // Check for changes resulting in a fetch
    if (helpers.viewPropsChanged(nextProps.viewOptions, this.props.viewOptions)) {
      this.props.getScans(
        helpers.createViewQueryObject(this.props.viewOptions, {
          scan_type: 'inspect'
        })
      );
    }

    if (nextProps.fulfilled && !this.props.fulfilled) {
      this.setState({ lastRefresh: Date.now() });
      this.startPolling();
    }
  }

  doUpdate() {
    this.forceUpdate();
  }

  startPolling() {
    if (!this.pollingInterval && this.mounted) {
      this.pollingInterval = setInterval(this.doUpdate, 3000);
    }
  }

  stopPolling() {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = null;
    }
  }

  notifyActionStatus(scan, actionText, error, results) {
    const { getScans, viewOptions } = this.props;

    if (error) {
      Store.dispatch({
        type: toastNotificationTypes.TOAST_ADD,
        alertType: 'error',
        header: 'Error',
        message: helpers.getErrorMessageFromResults(results)
      });
    } else {
      Store.dispatch({
        type: toastNotificationTypes.TOAST_ADD,
        alertType: 'success',
        message: (
          <span>
            Scan <strong>{scan.name}</strong> {actionText}.
          </span>
        )
      });

      getScans(
        helpers.createViewQueryObject(viewOptions, {
          scan_type: 'inspect'
        })
      );
    }
  }

  notifyDownloadStatus(error, results) {
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
        message: <span>Report downloaded.</span>
      });
    }
  }

  downloadSummaryReport(reportId) {
    this.props
      .getReportDeploymentsCsv(reportId)
      .then(response => this.notifyDownloadStatus(false), error => this.notifyDownloadStatus(true, error.message));
  }

  downloadDetailedReport(reportId) {
    this.props
      .getReportDetailsCsv(reportId)
      .then(response => this.notifyDownloadStatus(false), error => this.notifyDownloadStatus(true, error.message));
  }

  doStartScan(item) {
    this.props
      .startScan(item.id)
      .then(
        response => this.notifyActionStatus(item, 'started', false, response.value),
        error => this.notifyActionStatus(item, 'started', true, error.message)
      );
  }

  doPauseScan(item) {
    this.props
      .pauseScan(item.id)
      .then(
        response => this.notifyActionStatus(item, 'paused', false, response.value),
        error => this.notifyActionStatus(item, 'paused', true, error.message)
      );
  }

  doResumeScan(item) {
    this.props
      .restartScan(item.id)
      .then(
        response => this.notifyActionStatus(item, 'resumed', false, response.value),
        error => this.notifyActionStatus(item, 'resumed', true, error.message)
      );
  }

  doCancelScan(item) {
    this.props
      .cancelScan(item.id)
      .then(
        response => this.notifyActionStatus(item, 'canceled', false, response.value),
        error => this.notifyActionStatus(item, 'canceled', true, error.message)
      );
  }

  addSource() {
    Store.dispatch({
      type: sourcesTypes.CREATE_SOURCE_SHOW
    });
  }

  refresh() {
    this.props.getScans({ scan_type: 'inspect' });
  }

  clearFilters() {
    Store.dispatch({
      type: viewToolbarTypes.CLEAR_FILTERS,
      viewType: viewTypes.SCANS_VIEW
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

  renderScansList(items) {
    if (_.size(items)) {
      return (
        <ListView className="quipicords-list-view">
          {items.map((item, index) => (
            <ScanListItem
              item={item}
              key={index}
              onSummaryDownload={this.downloadSummaryReport}
              onDetailedDownload={this.downloadDetailedReport}
              onStart={this.doStartScan}
              onPause={this.doPauseScan}
              onResume={this.doResumeScan}
              onCancel={this.doCancelScan}
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
    const { error, errorMessage, scans, viewOptions } = this.props;
    const { lastRefresh } = this.state;

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

    if (_.size(scans) || _.size(viewOptions.activeFilters)) {
      return (
        <React.Fragment>
          <div className="quipucords-view-container">
            <ViewToolbar
              viewType={viewTypes.SCANS_VIEW}
              filterFields={ScanFilterFields}
              sortFields={ScanSortFields}
              onRefresh={this.refresh}
              lastRefresh={lastRefresh}
              itemsType="Scan"
              itemsTypePlural="Scans"
              {...viewOptions}
            />
            <ViewPaginationRow viewType={viewTypes.SCANS_VIEW} {...viewOptions} />
            <div className="quipucords-list-container">{this.renderScansList(scans)}</div>
          </div>
          {this.renderPendingMessage()}
        </React.Fragment>
      );
    }

    return (
      <React.Fragment>
        <SourcesEmptyState onAddSource={this.addSource} />
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
  getReportDeploymentsCsv: PropTypes.func,
  getReportDetailsCsv: PropTypes.func,
  fulfilled: PropTypes.bool,
  error: PropTypes.bool,
  errorMessage: PropTypes.string,
  pending: PropTypes.bool,
  scans: PropTypes.array,
  viewOptions: PropTypes.object
};

const mapDispatchToProps = (dispatch, ownProps) => ({
  getScans: queryObj => dispatch(getScans(queryObj)),
  startScan: id => dispatch(startScan(id)),
  pauseScan: id => dispatch(pauseScan(id)),
  restartScan: id => dispatch(restartScan(id)),
  cancelScan: id => dispatch(cancelScan(id)),
  getReportDeploymentsCsv: (id, query) => dispatch(getReportDeploymentsCsv(id, query)),
  getReportDetailsCsv: id => dispatch(getReportDetailsCsv(id))
});

const mapStateToProps = function(state) {
  return Object.assign({}, state.scans.view, state.scans.persist, {
    viewOptions: state.viewOptions[viewTypes.SCANS_VIEW]
  });
};

export default connect(mapStateToProps, mapDispatchToProps)(Scans);
