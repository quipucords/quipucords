import React from 'react';
import PropTypes from 'prop-types';
import { Modal, Button, Icon } from 'patternfly-react';
import _ from 'lodash';
import { connect, reduxActions, reduxTypes, store } from '../../redux';
import helpers from '../../common/helpers';

class MergeReportsDialog extends React.Component {
  onClose = () => {
    store.dispatch({
      type: reduxTypes.scans.MERGE_SCAN_DIALOG_HIDE
    });
  };

  onMergeScanResults = () => {
    const { mergeScans, details, getMergedScanReportDetailsCsv, getMergedScanReportSummaryCsv } = this.props;
    const data = { reports: this.getValidReportId() };

    mergeScans(data).then(
      response => {
        if (details) {
          getMergedScanReportDetailsCsv(_.get(response, 'value.data.report_id')).then(
            () => this.notifyDownloadStatus(false),
            error => this.notifyDownloadStatus(true, error)
          );
        } else {
          getMergedScanReportSummaryCsv(_.get(response, 'value.data.report_id')).then(
            () => this.notifyDownloadStatus(false),
            error => this.notifyDownloadStatus(true, error)
          );
        }
      },
      error => this.notifyDownloadStatus(true, error)
    );
  };

  getValidScans() {
    const { scans } = this.props;
    return _.filter(scans, scan => _.get(scan, 'most_recent.status') === 'completed');
  }

  getInvalidScans() {
    const { scans } = this.props;
    return _.filter(scans, scan => _.get(scan, 'most_recent.status') !== 'completed');
  }

  getValidReportId() {
    return this.getValidScans().map(scan => scan.most_recent.report_id);
  }

  notifyDownloadStatus(error, results) {
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

    this.onClose();
  }

  renderValidScans() {
    const validScans = this.getValidScans();

    if (_.size(validScans)) {
      return (
        <div>
          <span>Scans to be included in the merged report:</span>
          <ul>
            {validScans.map(scan => (
              <li key={scan.id}>{scan.name}</li>
            ))}
          </ul>
        </div>
      );
    }

    return null;
  }

  renderInvalidScans() {
    const invalidScans = this.getInvalidScans();

    if (_.size(invalidScans)) {
      return (
        <div>
          <span>Failed scans that cannot be included in the merged report:</span>
          <ul>
            {invalidScans.map(scan => (
              <li key={scan.id}>{scan.name}</li>
            ))}
          </ul>
        </div>
      );
    }

    return null;
  }

  renderButtons() {
    const validCount = _.size(this.getValidScans());

    if (validCount === 0) {
      return (
        <Button bsStyle="primary" className="btn-cancel" onClick={this.onClose}>
          Close
        </Button>
      );
    }

    return (
      <React.Fragment>
        <Button bsStyle="default" className="btn-cancel" onClick={this.onClose}>
          Cancel
        </Button>
        <Button bsStyle="primary" type="submit" disabled={validCount < 2} onClick={this.onMergeScanResults}>
          Merge
        </Button>
      </React.Fragment>
    );
  }

  render() {
    const { show, scans, details } = this.props;

    if (!scans || scans.length === 0 || !scans[0]) {
      return null;
    }

    const validCount = _.size(this.getValidScans());
    const invalidCount = _.size(this.getInvalidScans());

    let icon;
    let heading;
    let footer = <span>Once the scan reports are merged, the results will be downloaded to your local machine.</span>;

    if (validCount < 2) {
      icon = <Icon type="pf" name="error-circle-o" />;
      heading = (
        <h3 className="merge-reports-heading">
          This action is invalid. You must select at least two scans with successful most recent scans.
        </h3>
      );
      footer = null;
    } else if (invalidCount > 0) {
      icon = <Icon type="pf" name="warning-triangle-o" />;
      heading = (
        <h3 className="merge-reports-heading">
          Warning, only the selected scans with successful most recent scans will be included in the report.
        </h3>
      );
    } else {
      icon = <Icon type="pf" name="info" />;
    }

    return (
      <Modal show={show} onHide={this.onClose}>
        <Modal.Header>
          <button type="button" className="close" onClick={this.onClose} aria-hidden="true" aria-label="Close">
            <Icon type="pf" name="close" />
          </button>
          <Modal.Title>{`${details ? 'Detailed' : 'Summary'} Merge Report`}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <div className="merge-reports-body">
            <span className="merge-reports-icon">{icon}</span>
            <span>
              {heading}
              <div>
                {this.renderValidScans()}
                {this.renderInvalidScans()}
                {footer}
              </div>
            </span>
          </div>
        </Modal.Body>
        <Modal.Footer>{this.renderButtons()}</Modal.Footer>
      </Modal>
    );
  }
}

MergeReportsDialog.propTypes = {
  mergeScans: PropTypes.func,
  getMergedScanReportDetailsCsv: PropTypes.func,
  getMergedScanReportSummaryCsv: PropTypes.func,
  show: PropTypes.bool.isRequired,
  scans: PropTypes.array,
  details: PropTypes.bool.isRequired
};

MergeReportsDialog.defaultProps = {
  mergeScans: helpers.noop,
  getMergedScanReportDetailsCsv: helpers.noop,
  getMergedScanReportSummaryCsv: helpers.noop,
  scans: []
};

const mapDispatchToProps = dispatch => ({
  mergeScans: data => dispatch(reduxActions.reports.mergeScanReports(data)),
  getMergedScanReportDetailsCsv: id => dispatch(reduxActions.reports.getMergedScanReportDetailsCsv(id)),
  getMergedScanReportSummaryCsv: id => dispatch(reduxActions.reports.getMergedScanReportSummaryCsv(id))
});

const mapStateToProps = state => ({
  ...state.scans.merge_dialog
});

const ConnectedMergeReportsDialog = connect(
  mapStateToProps,
  mapDispatchToProps
)(MergeReportsDialog);

export { ConnectedMergeReportsDialog as default, ConnectedMergeReportsDialog, MergeReportsDialog };
