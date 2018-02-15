import PropTypes from 'prop-types';
import React from 'react';
import { connect } from 'react-redux';

import {
  Alert,
  Button,
  EmptyState,
  Icon,
  ListView,
  Modal
} from 'patternfly-react';

import {
  getScans,
  pauseScan,
  cancelScan,
  restartScan
} from '../../redux/actions/scansActions';
import {
  sourcesTypes,
  toastNotificationTypes,
  viewTypes
} from '../../redux/constants';
import Store from '../../redux/store';
import helpers from '../../common/helpers';

import ViewToolbar from '../viewToolbar/viewToolbar';
import ViewPaginationRow from '../viewPaginationRow/viewPaginationRow';

import SourcesEmptyState from '../sources/sourcesEmptyState';
import { ScanListItem } from './scanListItem';
import { ScanFilterFields, ScanSortFields } from './scanConstants';

class Scans extends React.Component {
  constructor() {
    super();

    helpers.bindMethods(this, [
      'downloadSummaryReport',
      'downloadDetailedReport',
      'doPauseScan',
      'doCancelScan',
      'doStartScan',
      'doResumeScan',
      'addSource',
      'importSources',
      'refresh',
      'notifyActionStatus'
    ]);
    this.state = {
      selectedItems: []
    };
  }

  componentDidMount() {
    this.props.getScans(
      helpers.createViewQueryObject(this.props.viewOptions, {
        scan_type: 'inspect'
      })
    );
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps.scans && nextProps.scans !== this.props.scans) {
      nextProps.scans.forEach(scan => {
        scan.systems_scanned = Math.abs(scan.systems_scanned) % 100;
        scan.systems_failed = Math.abs(scan.systems_failed) % 100;
        scan.scans_count = Math.floor(Math.random() * 10);

        // TODO: Get real hosts or wait until expansion?
        scan.hosts = [];
        for (let i = 0; i < scan.systems_scanned; i++) {
          scan.hosts.push('host' + (i + 1));
        }
        scan.failed_hosts = [];
        for (let i = 0; i < scan.systems_failed; i++) {
          scan.failed_hosts.push('failedHost' + (i + 1));
        }
      });

      this.setState({ selectedItems: [] });
    }

    // Check for changes resulting in a fetch
    if (
      helpers.viewPropsChanged(nextProps.viewOptions, this.props.viewOptions)
    ) {
      this.props.getScans(
        helpers.createViewQueryObject(this.props.viewOptions, {
          scan_type: 'inspect'
        })
      );
    }
  }

  notifyActionStatus(actionText, error, results) {
    const { getScans, viewOptions } = this.props;
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
            Scan <strong>${results.id}</strong> {actionText}.
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

  downloadSummaryReport() {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: 'NYI',
      message: 'Downloading summary reports is not yet implemented'
    });
  }

  downloadDetailedReport() {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: 'NYI',
      message: 'Downloading summary reports is not yet implemented'
    });
  }

  doStartScan(item) {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: 'NYI',
      message: 'Start scan is not yet implemented'
    });
  }

  doPauseScan(item) {
    this.props
      .pauseScan(item.id)
      .then(
        response => this.notifyActionStatus('paused', false, response.value),
        error => this.notifyActionStatus('paused', true, error.message)
      );
  }

  doResumeScan(item) {
    this.props
      .restartScan(item.id)
      .then(
        response => this.notifyActionStatus('resumed', false, response.value),
        error => this.notifyActionStatus('resumed', true, error.message)
      );
  }

  doCancelScan(item) {
    this.props
      .cancelScan(item.id)
      .then(
        response => this.notifyActionStatus('canceled', false, response.value),
        error => this.notifyActionStatus('canceled', true, error.message)
      );
  }

  addSource() {
    Store.dispatch({
      type: sourcesTypes.EDIT_SOURCE_SHOW
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
    this.props.getScans({ scan_type: 'inspect' });
  }

  renderScanActions() {
    return (
      <div className="form-group">
        <Button onClick={this.refresh} bsStyle="success">
          <Icon type="fa" name="refresh" />
        </Button>
      </div>
    );
  }

  renderScansList(items) {
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

  render() {
    const { pending, error, errorMessage, scans, viewOptions } = this.props;

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
    if (error) {
      return (
        <EmptyState>
          <Alert type="error">
            <span>Error retrieving scans: {errorMessage}</span>
          </Alert>
        </EmptyState>
      );
    }
    if (scans && scans.length) {
      return (
        <div className="quipucords-view-container">
          <ViewToolbar
            viewType={viewTypes.SCANS_VIEW}
            filterFields={ScanFilterFields}
            sortFields={ScanSortFields}
            actions={this.renderScanActions()}
            itemsType="Scan"
            itemsTypePlural="Scans"
            {...viewOptions}
          />
          <div className="quipucords-list-container">
            {this.renderScansList(scans)}
          </div>
          <ViewPaginationRow viewType={viewTypes.SCANS_VIEW} {...viewOptions} />
        </div>
      );
    }
    return (
      <SourcesEmptyState
        onAddSource={this.addSource}
        onImportSources={this.importSources}
      />
    );
  }
}

Scans.propTypes = {
  getScans: PropTypes.func,
  pauseScan: PropTypes.func,
  cancelScan: PropTypes.func,
  restartScan: PropTypes.func,
  error: PropTypes.bool,
  errorMessage: PropTypes.string,
  pending: PropTypes.bool,
  scans: PropTypes.array,
  viewOptions: PropTypes.object
};

const mapDispatchToProps = (dispatch, ownProps) => ({
  getScans: queryObj => dispatch(getScans(queryObj)),
  pauseScan: id => dispatch(pauseScan(id)),
  restartScan: id => dispatch(restartScan(id)),
  cancelScan: id => dispatch(cancelScan(id))
});

const mapStateToProps = function(state) {
  return Object.assign({}, state.scans.view, state.scans.persist, {
    viewOptions: state.viewOptions[viewTypes.SCANS_VIEW]
  });
};

export default connect(mapStateToProps, mapDispatchToProps)(Scans);
