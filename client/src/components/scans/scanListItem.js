import React from 'react';
import PropTypes from 'prop-types';
import cx from 'classnames';
import { Button, Checkbox, DropdownButton, Grid, Icon, ListView, MenuItem } from 'patternfly-react';
import _ from 'lodash';
import * as moment from 'moment';
import { connect, reduxTypes, store } from '../../redux';
import { helpers } from '../../common/helpers';
import SimpleTooltip from '../simpleTooltIp/simpleTooltip';
import ScanSourceList from './scanSourceList';
import ScanHostList from '../scanHostList/scanHostList';
import ScanJobsList from './scanJobsList';
import ListStatusItem from '../listStatusItem/listStatusItem';

class ScanListItem extends React.Component {
  static isSelected(item, selectedSources) {
    return _.find(selectedSources, nextSelected => nextSelected.id === item.id) !== undefined;
  }

  componentWillReceiveProps(nextProps) {
    const { lastRefresh } = this.props;
    // Check for changes resulting in a fetch
    if (!_.isEqual(nextProps.lastRefresh, lastRefresh)) {
      this.closeExpandIfNoData(this.expandType());
    }
  }

  onToggleExpand = expandType => {
    const { item } = this.props;

    if (expandType === this.expandType()) {
      store.dispatch({
        type: reduxTypes.view.EXPAND_ITEM,
        viewType: reduxTypes.view.SCANS_VIEW,
        item
      });
    } else {
      store.dispatch({
        type: reduxTypes.view.EXPAND_ITEM,
        viewType: reduxTypes.view.SCANS_VIEW,
        item,
        expandType
      });
    }
  };

  onCloseExpand = () => {
    const { item } = this.props;
    store.dispatch({
      type: reduxTypes.view.EXPAND_ITEM,
      viewType: reduxTypes.view.SCANS_VIEW,
      item
    });
  };

  onItemSelectChange = () => {
    const { item, selectedScans } = this.props;

    store.dispatch({
      type: ScanListItem.isSelected(item, selectedScans) ? reduxTypes.view.DESELECT_ITEM : reduxTypes.view.SELECT_ITEM,
      viewType: reduxTypes.view.SCANS_VIEW,
      item
    });
  };

  expandType() {
    const { item, expandedScans } = this.props;

    return _.get(_.find(expandedScans, nextExpanded => nextExpanded.id === item.id), 'expandType');
  }

  closeExpandIfNoData(expandType) {
    const { item } = this.props;

    const successHosts = _.get(item, 'most_recent.systems_scanned', 0);
    const failedHosts = _.get(item, 'most_recent.systems_failed', 0);
    const prevCount = Math.max(_.get(item, 'jobs', []).length - 1, 0);

    if (
      (expandType === 'systemsScanned' && successHosts === 0) ||
      (expandType === 'systemsFailed' && failedHosts === 0) ||
      (expandType === 'jobs' && prevCount === 0)
    ) {
      this.onCloseExpand();
    }
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

    const expandType = this.expandType();
    const sourcesCount = item.sources ? item.sources.length : 0;
    const prevCount = Math.max(_.get(item, 'jobs', []).length - 1, 0);
    const successHosts = _.get(item, 'most_recent.systems_scanned', 0);
    const failedHosts = _.get(item, 'most_recent.systems_failed', 0);

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
        toggleExpand={this.onToggleExpand}
        iconInfo={helpers.scanStatusIcon('success')}
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
        toggleExpand={this.onToggleExpand}
        iconInfo={helpers.scanStatusIcon('failed')}
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
        toggleExpand={this.onToggleExpand}
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
        toggleExpand={this.onToggleExpand}
      />
    ];
  }

  renderActions() {
    const { item, onSummaryDownload, onDetailedDownload, onPause, onCancel, onStart, onResume } = this.props;

    let downloadActions = null;
    if (_.get(item, 'most_recent.report_id')) {
      downloadActions = (
        <DropdownButton key="downLoadButton" title="Download" pullRight id={`downloadButton_${item.id}`}>
          <MenuItem eventKey="1" onClick={() => onSummaryDownload(_.get(item, 'most_recent.report_id'))}>
            Summary Report
          </MenuItem>
          <MenuItem eventKey="2" onClick={() => onDetailedDownload(_.get(item, 'most_recent.report_id'))}>
            Detailed Report
          </MenuItem>
        </DropdownButton>
      );
    }

    switch (_.get(item, 'most_recent.status')) {
      case 'completed':
        return (
          <React.Fragment>
            <SimpleTooltip key="startTip" id="startTip" tooltip="Run Scan">
              <Button key="restartButton" onClick={() => onStart(item)} bsStyle="link">
                <Icon type="pf" name="spinner2" aria-label="Start" />
              </Button>
            </SimpleTooltip>
            {downloadActions}
          </React.Fragment>
        );
      case 'failed':
      case 'canceled':
        return (
          <SimpleTooltip id="restartTip" tooltip="Retry Scan">
            <Button key="restartButton" onClick={() => onStart(item)} bsStyle="link">
              <Icon type="pf" name="spinner2" aria-label="Start" />
            </Button>
            {downloadActions}
          </SimpleTooltip>
        );
      case 'created':
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
            {downloadActions}
          </React.Fragment>
        );
      case 'paused':
        return (
          <SimpleTooltip id="resumeTip" tooltip="Resume Scan">
            <Button key="resumeButton" onClick={() => onResume(item)} bsStyle="link">
              <Icon type="fa" name="play" aria-label="Resume" />
            </Button>
            {downloadActions}
          </SimpleTooltip>
        );
      case 'pending':
        return (
          <React.Fragment>
            <SimpleTooltip key="stop" id="stopTip" tooltip="Cancel Scan">
              <Button onClick={() => onCancel(item)} bsStyle="link">
                <Icon type="fa" name="stop" aria-label="Stop" />
              </Button>
            </SimpleTooltip>
            {downloadActions}
          </React.Fragment>
        );
      default:
        return (
          <SimpleTooltip id="startTip" tooltip="Start Scan">
            <Button onClick={() => onStart(item)} bsStyle="link">
              <Icon type="fa" name="play" aria-label="Start" />
            </Button>
            {downloadActions}
          </SimpleTooltip>
        );
    }
  }

  static renderHostRow(host) {
    return (
      <React.Fragment>
        <Grid.Col xs={6} sm={4} md={3}>
          <span>
            <Icon type="pf" name={host.status === 'success' ? 'ok' : 'error-circle-o'} />
            &nbsp; {host.name}
          </span>
        </Grid.Col>
        <Grid.Col xs={6} sm={8} md={9}>
          {_.get(host, 'source.name')}
        </Grid.Col>
      </React.Fragment>
    );
  }

  renderExpansionContents() {
    const { item, onSummaryDownload, onDetailedDownload, lastRefresh } = this.props;

    switch (this.expandType()) {
      case 'systemsScanned':
        return (
          <ScanHostList
            scanId={item.most_recent.id}
            lastRefresh={lastRefresh}
            status="success"
            renderHostRow={ScanListItem.renderHostRow}
            useInspectionResults
          />
        );
      case 'systemsFailed':
        return (
          <ScanHostList
            scanId={item.most_recent.id}
            lastRefresh={lastRefresh}
            status="failed"
            renderHostRow={ScanListItem.renderHostRow}
            useConnectionResults
            useInspectionResults
          />
        );
      case 'sources':
        return <ScanSourceList scan={item} lastRefresh={lastRefresh} />;
      case 'jobs':
        return (
          <ScanJobsList
            scan={item}
            onSummaryDownload={onSummaryDownload}
            onDetailedDownload={onDetailedDownload}
            lastRefresh={lastRefresh}
          />
        );
      default:
        return null;
    }
  }

  render() {
    const { item, selectedScans } = this.props;
    const selected = ScanListItem.isSelected(item, selectedScans);

    const classes = cx({
      'quipucords-scan-list-item': true,
      'list-view-pf-top-align': true,
      active: selected
    });

    return (
      <ListView.Item
        key={item.id}
        className={classes}
        checkboxInput={<Checkbox checked={selected} bsClass="" onChange={this.onItemSelectChange} />}
        actions={this.renderActions()}
        leftContent={<div className="list-item-name">{item.name}</div>}
        description={this.renderDescription()}
        additionalInfo={this.renderStatusItems()}
        compoundExpand
        compoundExpanded={this.expandType() !== undefined}
        onCloseCompoundExpand={this.onCloseExpand}
      >
        {this.renderExpansionContents()}
      </ListView.Item>
    );
  }
}

ScanListItem.propTypes = {
  item: PropTypes.object.isRequired,
  lastRefresh: PropTypes.number,
  onSummaryDownload: PropTypes.func,
  onDetailedDownload: PropTypes.func,
  onPause: PropTypes.func,
  onCancel: PropTypes.func,
  onStart: PropTypes.func,
  onResume: PropTypes.func,
  selectedScans: PropTypes.array,
  expandedScans: PropTypes.array
};

ScanListItem.defaultProps = {
  lastRefresh: 0,
  onSummaryDownload: helpers.noop,
  onDetailedDownload: helpers.noop,
  onPause: helpers.noop,
  onCancel: helpers.noop,
  onStart: helpers.noop,
  onResume: helpers.noop,
  selectedScans: [],
  expandedScans: []
};

const mapStateToProps = state => ({
  expandedScans: state.viewOptions[reduxTypes.view.SCANS_VIEW].expandedItems,
  selectedScans: state.viewOptions[reduxTypes.view.SCANS_VIEW].selectedItems
});

const ConnectedScanListItem = connect(mapStateToProps)(ScanListItem);

export { ConnectedScanListItem as default, ConnectedScanListItem, ScanListItem };
