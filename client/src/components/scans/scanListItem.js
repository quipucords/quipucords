import React from 'react';
import PropTypes from 'prop-types';
import cx from 'classnames';
import { connect } from 'react-redux';
import { Button, Checkbox, DropdownButton, Icon, ListView, MenuItem } from 'patternfly-react';
import _ from 'lodash';
import * as moment from 'moment';
import { helpers } from '../../common/helpers';
import Store from '../../redux/store';
import { viewTypes } from '../../redux/constants';
import SimpleTooltip from '../simpleTooltIp/simpleTooltip';
import ScanSourceList from './scanSourceList';
import ScanHostsList from './scanHostList';
import ScanJobsList from './scanJobsList';
import ListStatusItem from '../listStatusItem/listStatusItem';
import { getInspectionScanResults, getScanJobs } from '../../redux/actions/scansActions';

class ScanListItem extends React.Component {
  constructor() {
    super();

    helpers.bindMethods(this, ['toggleExpand', 'closeExpand', 'itemSelectChange']);

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
        let successHosts = _.get(item, 'most_recent.systems_scanned', 0);
        let failedHosts = _.get(item, 'most_recent.systems_failed', 0);
        if (
          (expandType === 'systemsScanned' && successHosts === 0) ||
          (expandType === 'systemsFailed' && failedHosts === 0)
        ) {
          Store.dispatch({
            type: viewTypes.EXPAND_ITEM,
            viewType: viewTypes.SCANS_VIEW,
            item: item
          });
          return;
        }

        this.setState({
          scanResultsPending: true,
          scanResultsError: null
        });
        this.props
          .getInspectionScanResults(item.most_recent.id)
          .then(results => {
            this.setState({
              scanResultsPending: false,
              scanResults: _.get(results.value, 'data')
            });
          })
          .catch(error => {
            this.setState({
              scanResultsPending: true,
              scanResultsError: helpers.getErrorMessageFromResults(error)
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
              scanJobsError: helpers.getErrorMessageFromResults(error)
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
        type: viewTypes.EXPAND_ITEM,
        viewType: viewTypes.SCANS_VIEW,
        item: item
      });
    } else {
      Store.dispatch({
        type: viewTypes.EXPAND_ITEM,
        viewType: viewTypes.SCANS_VIEW,
        item: item,
        expandType: expandType
      });
      this.loadExpandData(expandType);
    }
  }

  closeExpand() {
    const { item } = this.props;
    Store.dispatch({
      type: viewTypes.EXPAND_ITEM,
      viewType: viewTypes.SCANS_VIEW,
      item: item
    });
  }

  isSelected(item, selectedSources) {
    return (
      _.find(selectedSources, nextSelected => {
        return nextSelected.id === item.id;
      }) !== undefined
    );
  }

  itemSelectChange() {
    const { item, selectedScans } = this.props;

    Store.dispatch({
      type: this.isSelected(item, selectedScans) ? viewTypes.DESELECT_ITEM : viewTypes.SELECT_ITEM,
      viewType: viewTypes.SCANS_VIEW,
      item: item
    });
  }

  renderDescription() {
    const { item } = this.props;
    const scanStatus = _.get(item, 'most_recent.status');
    const statusIconInfo = helpers.scanStatusIcon(scanStatus);
    const classes = cx('scan-status-icon', ...statusIconInfo.classNames);
    const icon = statusIconInfo ? (
      <Icon className={classes} type={statusIconInfo.type} name={statusIconInfo.name} />
    ) : null;

    let scanTime = _.get(item, 'most_recent.end_time');

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
                <Icon type="pf" name="spinner2" aria-label="Start" />
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
              <Icon type="pf" name="spinner2" aria-label="Start" />
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
                <Icon type="fa" name="pause" aria-label="Pause" />
              </Button>
            </SimpleTooltip>
            <SimpleTooltip key="stop" id="stopTip" tooltip="Cancel Scan">
              <Button onClick={() => onCancel(item)} bsStyle="link">
                <Icon type="fa" name="stop" aria-label="Stop" />
              </Button>
            </SimpleTooltip>
          </React.Fragment>
        );
      case 'paused':
        return (
          <SimpleTooltip id="resumeTip" tooltip="Resume Scan">
            <Button key="resumeButton" onClick={() => onResume(item)} bsStyle="link">
              <Icon type="fa" name="play" aria-label="Resume" />
            </Button>
          </SimpleTooltip>
        );
      default:
        return (
          <SimpleTooltip id="startTip" tooltip="Start Scan">
            <Button onClick={() => onStart(item)} bsStyle="link">
              <Icon type="fa" name="play" aria-label="Start" />
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
    const { item, selectedScans } = this.props;
    const selected = this.isSelected(item, selectedScans);

    const classes = cx({
      'quipucords-scan-list-item': true,
      'list-view-pf-top-align': true,
      active: selected
    });

    return (
      <ListView.Item
        key={item.id}
        className={classes}
        checkboxInput={<Checkbox checked={selected} bsClass="" onChange={this.itemSelectChange} />}
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
  getInspectionScanResults: PropTypes.func,
  getScanJobs: PropTypes.func,
  selectedScans: PropTypes.array,
  expandedScans: PropTypes.array
};

const mapStateToProps = function(state) {
  return Object.assign({
    expandedScans: state.viewOptions[viewTypes.SCANS_VIEW].expandedItems,
    selectedScans: state.viewOptions[viewTypes.SCANS_VIEW].selectedItems
  });
};

const mapDispatchToProps = (dispatch, ownProps) => ({
  getInspectionScanResults: id => dispatch(getInspectionScanResults(id)),
  getScanJobs: id => dispatch(getScanJobs(id))
});

export default connect(mapStateToProps, mapDispatchToProps)(ScanListItem);
