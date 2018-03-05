import _ from 'lodash';
import * as moment from 'moment';
import React from 'react';
import cx from 'classnames';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';

import { Button, DropdownButton, Icon, ListView, MenuItem } from 'patternfly-react';

import { helpers } from '../../common/helpers';

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
  }

  toggleExpand(expandType) {
    const { item } = this.props;

    if (expandType === item.expandType) {
      item.expanded = !item.expanded;
    } else {
      item.expanded = true;
      item.expandType = expandType;
      if (expandType === 'systemsScanned' || expandType === 'systemsFailed') {
        if (!item.scanResults) {
          item.scanResultsPending = true;
          item.scanResultsError = null;
          this.props
            .getScanResults(item.id)
            .then(results => {
              item.scanResultsPending = false;
              item.scanResults = _.get(results.value, 'data');
            })
            .catch(error => {
              item.scanResultsPending = false;
              item.scanResultsError = _.get(error.payload, 'response.request.responseText', error.payload.message);
            })
            .finally(() => {
              item.scanResultsPending = false;
              this.forceUpdate();
            });
        }
      } else if (expandType === 'jobs') {
        if (!item.scanJobs) {
          item.scanJobsPending = true;
          item.scanJobsError = null;
          this.props
            .getScanJobs(item.id)
            .then(results => {
              item.scanJobsPending = false;
              item.scanJobs = _.get(results.value, 'data.results');
            })
            .catch(error => {
              item.scanJobsPending = false;
              item.scanJobsError = _.get(error.payload, 'response.request.responseText', error.payload.message);
            })
            .finally(() => {
              item.scanJobsPending = false;
              this.forceUpdate();
            });
        }
      }
    }
    this.forceUpdate();
  }

  closeExpand() {
    const { item } = this.props;
    item.expanded = false;
    this.forceUpdate();
  }

  renderDescription() {
    const { item } = this.props;

    let scanDescription = '';

    let icon = null;
    let scanTime = _.get(item, 'most_recent.end_time');

    switch (_.get(item, 'most_recent.status')) {
      case 'completed':
        scanDescription = 'Last Scanned';
        icon = <Icon className="scan-status-icon" type="pf" name="ok" />;
        break;
      case 'failed':
        scanDescription = 'Scan Failed';
        icon = <Icon className="scan-status-icon" type="pf" name="error-circle-o" />;
        break;
      case 'canceled':
        scanDescription = 'Scan Canceled';
        icon = <Icon className="scan-status-icon" type="pf" name="error-circle-o" />;
        break;
      case 'created':
        scanDescription = 'Scan Created';
        icon = <Icon className="scan-status-icon invisible" type="fa" name="spinner" />;
        break;
      case 'pending':
        scanDescription = 'Scan Pending';
        icon = <Icon className="scan-status-icon invisible" type="fa" name="spinner" />;
        scanTime = _.get(item, 'most_recent.start_time');
        break;
      case 'running':
        scanDescription = 'Scan in Progress';
        icon = <Icon className="scan-status-icon fa-spin" type="fa" name="spinner" />;
        scanTime = _.get(item, 'most_recent.start_time');
        break;
      case 'paused':
        scanDescription = 'Scan Paused';
        icon = <Icon className="scan-status-icon" type="pf" name="warning-triangle-o" />;
        break;
      default:
        return null;
    }

    return (
      <div className="scan-description">
        {icon}
        <div className="scan-status-text">
          <div>{scanDescription}</div>
          <div className="text-muted">
            {moment
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
        expanded={item.expanded && item.expandType === 'systemsScanned'}
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
        expanded={item.expanded && item.expandType === 'systemsFailed'}
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
        expanded={item.expanded && item.expandType === 'sources'}
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
        expanded={item.expanded && item.expandType === 'jobs'}
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

    switch (item.expandType) {
      case 'systemsScanned':
        return <ScanHostsList scan={item} status="success" />;
      case 'systemsFailed':
        return <ScanHostsList scan={item} status="failed" />;
      case 'sources':
        return <ScanSourceList scan={item} />;
      case 'jobs':
        return (
          <ScanJobsList scan={item} onSummaryDownload={onSummaryDownload} onDetailedDownload={onDetailedDownload} />
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
        compoundExpanded={item.expanded}
        onCloseCompoundExpand={this.closeExpand}
      >
        {this.renderExpansionContents()}
      </ListView.Item>
    );
  }
}

ScanListItem.propTypes = {
  item: PropTypes.object,
  onSummaryDownload: PropTypes.func,
  onDetailedDownload: PropTypes.func,
  onPause: PropTypes.func,
  onCancel: PropTypes.func,
  onStart: PropTypes.func,
  onResume: PropTypes.func,
  getScanResults: PropTypes.func,
  getScanJobs: PropTypes.func
};

const mapStateToProps = function(state) {
  return {};
};

const mapDispatchToProps = (dispatch, ownProps) => ({
  getScanResults: id => dispatch(getScanResults(id)),
  getScanJobs: id => dispatch(getScanJobs(id))
});

export default connect(mapStateToProps, mapDispatchToProps)(ScanListItem);
