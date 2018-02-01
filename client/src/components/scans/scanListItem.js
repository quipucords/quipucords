import React from 'react';
import PropTypes from 'prop-types';
import JSONPretty from 'react-json-pretty';
import {
  Button,
  DropdownButton,
  Icon,
  ListView,
  MenuItem
} from 'patternfly-react';

import { bindMethods } from '../../common/helpers';

import { SimpleTooltip } from '../simpleTooltIp/simpleTooltip';
import { ScanSourceList } from './scanSourceList';
import { ScanHostsList } from './scanHostList';

class ScanListItem extends React.Component {
  constructor() {
    super();

    bindMethods(this, ['toggleExpand', 'closeExpand']);

    this.state = {
      expanded: false,
      expandType: 'credentials'
    };
  }

  toggleExpand(expandType) {
    if (expandType === this.state.expandType) {
      this.setState({ expanded: !this.state.expanded });
    } else {
      this.setState({ expanded: true, expandType: expandType });
    }
  }

  closeExpand() {
    this.setState({ expanded: false });
  }

  renderScanType() {
    const { item } = this.props;

    let itemIconType;
    let itemIconName;
    let scanTypeText;
    switch (item.scan_type) {
      case 'connect':
        itemIconType = 'pf';
        itemIconName = 'connected';
        scanTypeText = 'Connection Scan';
        break;
      case 'inspect':
        itemIconType = 'fa';
        itemIconName = 'search';
        scanTypeText = 'Inspection Scan';
        break;
      default:
        itemIconType = '';
        itemIconName = '';
        scanTypeText = '';
    }

    return (
      <SimpleTooltip id="scanTypeTip" tooltip={scanTypeText}>
        <ListView.Icon type={itemIconType} name={itemIconName} />
      </SimpleTooltip>
    );
  }

  renderDescription() {
    const { item } = this.props;

    let scanDescription = '';

    let icon = null;
    switch (item.status) {
      case 'completed':
        scanDescription = 'Last Scanned';
        icon = <Icon className="scan-status-icon" type="pf" name="ok" />;
        break;
      case 'failed':
        scanDescription = 'Scan Failed';
        icon = (
          <Icon className="scan-status-icon" type="pf" name="error-circle-o" />
        );
        break;
      case 'canceled':
        scanDescription = 'Scan Canceled';
        icon = (
          <Icon className="scan-status-icon" type="pf" name="error-circle-o" />
        );
        break;
      case 'created':
        scanDescription = 'Scan Created';
        icon = (
          <Icon
            className="scan-status-icon invisible"
            type="fa"
            name="spinner"
          />
        );
        break;
      case 'pending':
        scanDescription = 'Scan Pending';
        icon = (
          <Icon
            className="scan-status-icon invisible"
            type="fa"
            name="spinner"
          />
        );
        break;
      case 'running':
        scanDescription = 'Scan in Progress';
        icon = (
          <Icon className="scan-status-icon fa-spin" type="fa" name="spinner" />
        );
        break;
      case 'paused':
        scanDescription = 'Scan Paused';
        icon = (
          <Icon
            className="scan-status-icon"
            type="pf"
            name="warning-triangle-o"
          />
        );
        break;
      default:
        return null;
    }

    return (
      <div className="scan-description">
        {icon}
        <div className="scan-status-text">
          <div>{scanDescription}</div>
          <div>Started 5 min ago</div>
        </div>
      </div>
    );
  }

  renderStatusItems() {
    const { item } = this.props;
    const { expanded, expandType } = this.state;

    let sourcesCount = item.sources ? item.sources.length : 0;

    return [
      <ListView.InfoItem
        key="systemsScanned"
        className={
          'list-view-info-item-text-count ' +
          (item.systems_scanned === 0 ? 'invisible' : '')
        }
      >
        <SimpleTooltip
          id="okHostsTip"
          tooltip={
            item.systems_scanned +
            (item.systems_scanned === 1
              ? ' Successful System'
              : ' Successful Systems')
          }
        >
          <ListView.Expand
            expanded={expanded && expandType === 'systemsScanned'}
            toggleExpanded={() => {
              this.toggleExpand('systemsScanned');
            }}
          >
            <Icon
              className="list-view-compound-item-icon"
              type="pf"
              name="ok"
            />
            <strong>{item.systems_scanned}</strong>
          </ListView.Expand>
        </SimpleTooltip>
      </ListView.InfoItem>,
      <ListView.InfoItem
        key="systemsFailed"
        className={
          'list-view-info-item-text-count ' +
          (item.systems_failed === 0 ? 'invisible' : '')
        }
      >
        <SimpleTooltip
          id="failedHostsTip"
          tooltip={
            item.systems_failed +
            (item.systems_failed === 1 ? ' Failed System' : ' Failed Systems')
          }
        >
          <ListView.Expand
            expanded={expanded && expandType === 'systemsFailed'}
            toggleExpanded={() => {
              this.toggleExpand('systemsFailed');
            }}
          >
            <Icon
              className="list-view-compound-item-icon"
              type="pf"
              name="error-circle-o"
            />
            <strong>{item.systems_failed}</strong>
          </ListView.Expand>
        </SimpleTooltip>
      </ListView.InfoItem>,
      <ListView.InfoItem
        key="sources"
        className="list-view-info-item-text-count"
      >
        <ListView.Expand
          expanded={expanded && expandType === 'sources'}
          toggleExpanded={() => {
            this.toggleExpand('sources');
          }}
        >
          <strong>{sourcesCount} </strong>
          {sourcesCount === 1 ? ' Source' : ' Sources'}
        </ListView.Expand>
      </ListView.InfoItem>,
      <ListView.InfoItem
        key="scansCount"
        className={
          'list-view-info-item-text-count ' +
          (item.scans_count === 0 ? 'invisible' : '')
        }
      >
        <ListView.Expand
          expanded={expanded && expandType === 'scans'}
          toggleExpanded={() => {
            this.toggleExpand('scans');
          }}
        >
          <strong>{item.scans_count} </strong>
          {item.scans_count === 1 ? ' Scan' : ' Scans'}
        </ListView.Expand>
      </ListView.InfoItem>
    ];
  }

  renderActions() {
    const {
      item,
      onSummaryDownload,
      onDetailedDownload,
      onPause,
      onCancel,
      onStart,
      onResume
    } = this.props;

    switch (item.status) {
      case 'completed':
        return [
          <SimpleTooltip key="startTip" id="startTip" tooltip="Run Scan">
            <Button
              key="restartButton"
              onClick={() => onStart(item)}
              bsStyle="link"
            >
              <Icon type="pf" name="spinner2" atria-label="Start" />
            </Button>
          </SimpleTooltip>,
          <DropdownButton
            key="downLoadButton"
            bsStyle="primary"
            title="Download"
            pullRight
            id={`downloadButton_${item.id}`}
          >
            <MenuItem eventKey="1" onClick={onSummaryDownload}>
              Summary Report
            </MenuItem>
            <MenuItem eventKey="2" onClick={onDetailedDownload}>
              Detailed Report
            </MenuItem>
          </DropdownButton>
        ];
      case 'failed':
      case 'canceled':
        return (
          <SimpleTooltip id="restartTip" tooltip="Retry Scan">
            <Button
              key="restartButton"
              onClick={() => onStart(item)}
              bsStyle="link"
            >
              <Icon type="pf" name="spinner2" atria-label="Start" />
            </Button>
          </SimpleTooltip>
        );
      case 'created':
      case 'pending':
      case 'running':
        return [
          <SimpleTooltip key="pauseButton" id="pauseTip" tooltip="Pause Scan">
            <Button onClick={() => onPause(item)} bsStyle="link">
              <Icon type="fa" name="pause" atria-label="Pause" />
            </Button>
          </SimpleTooltip>,
          <SimpleTooltip key="stop" id="stopTip" tooltip="Cancel Scan">
            <Button onClick={() => onCancel(item)} bsStyle="link">
              <Icon type="fa" name="stop" atria-label="Stop" />
            </Button>
          </SimpleTooltip>
        ];
      case 'paused':
        return (
          <SimpleTooltip id="resumeTip" tooltip="Resume Scan">
            <Button
              key="resumeButton"
              onClick={() => onResume(item)}
              bsStyle="link"
            >
              <Icon type="fa" name="play" atria-label="Resume" />
            </Button>
          </SimpleTooltip>
        );
      default:
        return null;
    }
  }

  renderExpansionContents() {
    const { item } = this.props;
    const { expandType } = this.state;

    switch (expandType) {
      case 'systemsScanned':
        return <ScanHostsList hosts={item.hosts} status="ok" />;
      case 'systemsFailed':
        return (
          <ScanHostsList hosts={item.failed_hosts} status="error-circle-o" />
        );
      case 'sources':
        return <ScanSourceList scan={item} />;
      case 'scans':
        return <JSONPretty json={item} />;
      default:
        return <JSONPretty json={item} />;
    }
  }

  render() {
    const { item } = this.props;
    const { expanded } = this.state;

    return (
      <ListView.Item
        key={item.id}
        actions={this.renderActions()}
        leftContent={this.renderScanType()}
        heading={`ID: ${item.id}`}
        description={this.renderDescription()}
        additionalInfo={this.renderStatusItems()}
        compoundExpand
        compoundExpanded={expanded}
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
  onResume: PropTypes.func
};

export { ScanListItem };
