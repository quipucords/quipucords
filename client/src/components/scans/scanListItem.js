import _ from 'lodash';
import * as moment from 'moment';
import React from 'react';
import cx from 'classnames';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';

import { Button, DropdownButton, Icon, ListView, MenuItem } from 'patternfly-react';

import { helpers } from '../../common/helpers';
import Store from '../../redux/store';
import { scansTypes } from '../../redux/constants';

import { SimpleTooltip } from '../simpleTooltIp/simpleTooltip';
import { ScanSourceList } from './scanSourceList';
import ScanHostsList from './scanHostList';
import ScanJobsList from './scanJobsList';
import ListStatusItem from '../listStatusItem/listStatusItem';
import { getScanResults, getScanJobs } from '../../redux/actions/scansActions';

class ScanListItem extends React.Component {
  constructor() {
    super();

    helpers.bindMethods(this, ['toggleExpand', 'closeExpand']);

    this.state = {
      scanResultsPending: false,
      scanResultsError: null,
      scanResults: null,
      scanJobsPending: false,
      scanJobsError: null,
      scanJobs: null
    };
  }

  componentWillReceiveProps(nextProps) {
    // Check for changes resulting in a fetch
    if (!_.isEqual(nextProps.lastRefresh, this.props.lastRefresh)) {
      this.loadExpandData(this.expandType());
    }
  }

  expandType() {
    const { item, expandedScans } = this.props;

    return _.get(
      _.find(expandedScans, nextExpanded => {
        return nextExpanded.id === item.id;
      }),
      'expandType'
    );
  }

  loadExpandData(expandType) {
    const { item } = this.props;

    switch (expandType) {
      case 'systemsScanned':
      case 'systemsFailed':
        this.setState({
          scanResultsPending: true,
          scanResultsError: null
        });
        this.props
          .getScanResults(item.id)
          .then(results => {
            this.setState({
              scanResultsPending: false,
              scanResults: _.get(results.value, 'data')
            });
          })
          .catch(error => {
            this.setState({
              scanResultsPending: true,
              scanResultsError: helpers.getErrorMessageFromResults(error.payload)
            });
          });
        break;
      case 'jobs':
        this.setState({
          scanJobsPending: true,
          scanJobsError: null
        });
        this.props
          .getScanJobs(item.id)
          .then(results => {
            this.setState({
              scanJobsPending: false,
              scanJobs: _.get(results.value, 'data.results')
            });
          })
          .catch(error => {
            this.setState({
              scanJobsPending: false,
              scanJobsError: helpers.getErrorMessageFromResults(error.payload)
            });
          });
        break;
      default:
        break;
    }
  }

  toggleExpand(expandType) {
    const { item } = this.props;

    if (expandType === this.expandType()) {
      Store.dispatch({
        type: scansTypes.EXPAND_SCAN,
        scan: item
      });
    } else {
      Store.dispatch({
        type: scansTypes.EXPAND_SCAN,
        scan: item,
        expandType: expandType
      });
      this.loadExpandData(expandType);
    }
  }

  closeExpand() {
    const { item } = this.props;
    Store.dispatch({
      type: scansTypes.EXPAND_SCAN,
      scan: item
    });
  }

  renderDescription() {
    const { item } = this.props;

    let scanTime = _.get(item, 'most_recent.end_time');
    let scanStatus = _.get(item, 'most_recent.status');
    let statusIconInfo = helpers.scanStatusIcon(scanStatus);
    let icon = statusIconInfo ? (
      <Icon className="scan-status-icon" type={statusIconInfo.type} name={statusIconInfo.name} />
    ) : null;

    if (scanStatus === 'pending' || scanStatus === 'running') {
      scanTime = _.get(item, 'most_recent.start_time');
    }

    return (
      <div className="scan-description">
        {icon}
        <div className="scan-status-text">
          <div>{_.get(item, 'most_recent.status_details.job_status_message', 'Scan created')}</div>
          <div className="text-muted">
            {scanTime &&
              moment
                .utc(scanTime)
                .utcOffset(moment().utcOffset())
                .fromNow()}
          </div>
        </div>
      </div>
    );
  }

  renderStatusItems() {
    const { item } = this.props;

    let expandType = this.expandType();
    let sourcesCount = item.sources ? item.sources.length : 0;
    let prevCount = Math.max(_.get(item, 'jobs', []).length - 1, 0);
    let successHosts = _.get(item, 'most_recent.systems_scanned', 0);
    let failedHosts = _.get(item, 'most_recent.systems_failed', 0);

    return [
      <ListStatusItem
        key="successHosts"
        id="successHosts"
        count={successHosts}
        emptyText="0 Successful"
        tipSingular="Successful System"
        tipPlural="Successful Systems"
        expanded={expandType === 'systemsScanned'}
        expandType="systemsScanned"
        toggleExpand={this.toggleExpand}
        iconType="pf"
        iconName="ok"
      />,
      <ListStatusItem
        key="systemsFailed"
        id="systemsFailed"
        count={failedHosts}
        emptyText="0 Failed"
        tipSingular="Failed System"
        tipPlural="Failed Systems"
        expanded={expandType === 'systemsFailed'}
        expandType="systemsFailed"
        toggleExpand={this.toggleExpand}
        iconType="pf"
        iconName="error-circle-o"
      />,
      <ListStatusItem
        key="sources"
        id="sources"
        count={sourcesCount}
        emptyText="0 Sources"
        tipSingular="Source"
        tipPlural="Sources"
        expanded={expandType === 'sources'}
        expandType="sources"
        toggleExpand={this.toggleExpand}
      />,
      <ListStatusItem
        key="scans"
        id="scans"
        count={prevCount}
        emptyText="0 Previous"
        tipSingular="Previous"
        tipPlural="Previous"
        expanded={expandType === 'jobs'}
        expandType="jobs"
        toggleExpand={this.toggleExpand}
      />
    ];
  }

  renderActions() {
    const { item, onSummaryDownload, onDetailedDownload, onPause, onCancel, onStart, onResume } = this.props;

    switch (_.get(item, 'most_recent.status')) {
      case 'completed':
        return (
          <React.Fragment>
            <SimpleTooltip key="startTip" id="startTip" tooltip="Run Scan">
              <Button key="restartButton" onClick={() => onStart(item)} bsStyle="link">
                <Icon type="pf" name="spinner2" atria-label="Start" />
              </Button>
            </SimpleTooltip>
            <DropdownButton key="downLoadButton" title="Download" pullRight id={`downloadButton_${item.id}`}>
              <MenuItem eventKey="1" onClick={() => onSummaryDownload(_.get(item, 'most_recent.report_id'))}>
                Summary Report
              </MenuItem>
              <MenuItem eventKey="2" onClick={() => onDetailedDownload(_.get(item, 'most_recent.report_id'))}>
                Detailed Report
              </MenuItem>
            </DropdownButton>
          </React.Fragment>
        );
      case 'failed':
      case 'canceled':
        return (
          <SimpleTooltip id="restartTip" tooltip="Retry Scan">
            <Button key="restartButton" onClick={() => onStart(item)} bsStyle="link">
              <Icon type="pf" name="spinner2" atria-label="Start" />
            </Button>
          </SimpleTooltip>
        );
      case 'created':
      case 'pending':
      case 'running':
        return (
          <React.Fragment>
            <SimpleTooltip key="pauseButton" id="pauseTip" tooltip="Pause Scan">
              <Button onClick={() => onPause(item)} bsStyle="link">
                <Icon type="fa" name="pause" atria-label="Pause" />
              </Button>
            </SimpleTooltip>
            <SimpleTooltip key="stop" id="stopTip" tooltip="Cancel Scan">
              <Button onClick={() => onCancel(item)} bsStyle="link">
                <Icon type="fa" name="stop" atria-label="Stop" />
              </Button>
            </SimpleTooltip>
          </React.Fragment>
        );
      case 'paused':
        return (
          <SimpleTooltip id="resumeTip" tooltip="Resume Scan">
            <Button key="resumeButton" onClick={() => onResume(item)} bsStyle="link">
              <Icon type="fa" name="play" atria-label="Resume" />
            </Button>
          </SimpleTooltip>
        );
      default:
        return (
          <SimpleTooltip id="startTip" tooltip="Start Scan">
            <Button onClick={() => onStart(item)} bsStyle="link">
              <Icon type="fa" name="play" atria-label="Start" />
            </Button>
          </SimpleTooltip>
        );
    }
  }

  renderExpansionContents() {
    const { item, onSummaryDownload, onDetailedDownload } = this.props;
    const { scanJobs, scanJobsError, scanJobsPending, scanResults, scanResultsError, scanResultsPending } = this.state;

    switch (this.expandType()) {
      case 'systemsScanned':
        return (
          <ScanHostsList
            scanResults={scanResults}
            scanResultsError={scanResultsError}
            scanResultsPending={scanResultsPending}
            status="success"
          />
        );
      case 'systemsFailed':
        return (
          <ScanHostsList
            scanResults={scanResults}
            scanResultsError={scanResultsError}
            scanResultsPending={scanResultsPending}
            status="failed"
          />
        );
      case 'sources':
        return <ScanSourceList scan={item} />;
      case 'jobs':
        return (
          <ScanJobsList
            scan={item}
            scanJobs={scanJobs}
            scanJobsError={scanJobsError}
            scanJobsPending={scanJobsPending}
            onSummaryDownload={onSummaryDownload}
            onDetailedDownload={onDetailedDownload}
          />
        );
      default:
        return null;
    }
  }

  render() {
    const { item } = this.props;

    const classes = cx({
      'quipucords-scan-list-item': true,
      'list-view-pf-top-align': true,
      active: item.selected
    });

    return (
      <ListView.Item
        key={item.id}
        className={classes}
        actions={this.renderActions()}
        leftContent={<strong>{item.name}</strong>}
        description={this.renderDescription()}
        additionalInfo={this.renderStatusItems()}
        compoundExpand
        compoundExpanded={this.expandType() !== undefined}
        onCloseCompoundExpand={this.closeExpand}
      >
        {this.renderExpansionContents()}
      </ListView.Item>
    );
  }
}

ScanListItem.propTypes = {
  item: PropTypes.object,
  lastRefresh: PropTypes.number,
  onSummaryDownload: PropTypes.func,
  onDetailedDownload: PropTypes.func,
  onPause: PropTypes.func,
  onCancel: PropTypes.func,
  onStart: PropTypes.func,
  onResume: PropTypes.func,
  getScanResults: PropTypes.func,
  getScanJobs: PropTypes.func,
  expandedScans: PropTypes.array
};

const mapStateToProps = function(state) {
  return Object.assign(state.scans.persist);
};

const mapDispatchToProps = (dispatch, ownProps) => ({
  getScanResults: id => dispatch(getScanResults(id)),
  getScanJobs: id => dispatch(getScanJobs(id))
});

export default connect(mapStateToProps, mapDispatchToProps)(ScanListItem);
