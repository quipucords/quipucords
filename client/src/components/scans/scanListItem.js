import React from 'react';
import PropTypes from 'prop-types';
import JSONPretty from 'react-json-pretty';
import {
  DropdownButton,
  DropdownKebab,
  Icon,
  ListView,
  MenuItem
} from 'patternfly-react';

import { bindMethods } from '../../common/helpers';

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

  renderExpansionContents() {
    const { item } = this.props;

    return <JSONPretty json={item} />;
  }

  render() {
    const {
      item,
      onSummaryDownload,
      onDetailedDownload,
      onPause,
      onCancel,
      onStart
    } = this.props;
    const { expanded, expandType } = this.state;

    let sourcesCount = item.sources ? item.sources.length : 0;

    let statusName = '';
    switch (item.status) {
      case 'completed':
        statusName = 'ok';
        break;
      case 'failed':
        statusName = 'error-circle-o';
        break;
      case 'canceled':
        statusName = 'warning-triangle-o';
        break;
      case 'created':
        statusName = 'add-circle-o';
        break;
      case 'running':
        statusName = 'on-running';
        break;
      case 'paused':
        statusName = 'paused';
        break;
      case 'pending':
        statusName = 'pending';
        break;
      default:
        statusName = '';
    }

    let itemIconType;
    let itemIconName;
    switch (item.scan_type) {
      case 'connect':
        itemIconType = 'pf';
        itemIconName = 'connected';
        break;
      case 'inspect':
        itemIconType = 'fa';
        itemIconName = 'search';
        break;
      default:
        itemIconType = '';
        itemIconName = '';
    }

    let leftContent = (
      <span>
        <ListView.Icon
          key="statusicon"
          className="scan-item-status"
          type="pf"
          name={statusName}
        />
        <ListView.Icon key="itemicon" type={itemIconType} name={itemIconName} />
      </span>
    );

    /** TODO: Saving to be put in expansion area
     let heading = item.sources.map((source, index) => {
      let sourceIcon;
      switch (source.source_type) {
        case 'vcenter':
          sourceIcon = <Icon type="pf" name="virtual-machine" />;
          break;
        case 'network':
          sourceIcon = <Icon type="pf" name="network" />;
          break;
        default:
          sourceIcon = null;
      }
      return (
        <div key={index}>
          {sourceIcon}
          <span className="scan-list-source-name">{source.name}</span>
        </div>
      );
    });
     */

    return (
      <ListView.Item
        key={item.id}
        actions={
          <span>
            <DropdownButton
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
            <DropdownKebab
              id={`dropdownActions_${item.id}`}
              key="kebab"
              pullRight
            >
              <MenuItem onClick={() => onPause(item)}>Pause</MenuItem>
              <MenuItem onClick={() => onCancel(item)}>Cancel</MenuItem>
              <MenuItem divider />
              <MenuItem onClick={() => onStart(item)}>Start Scan</MenuItem>
            </DropdownKebab>
          </span>
        }
        leftContent={leftContent}
        heading={`ID: ${item.id}`}
        additionalInfo={[
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
              {sourcesCount} {sourcesCount === 1 ? ' Source' : ' Sources'}
            </ListView.Expand>
          </ListView.InfoItem>,
          <ListView.InfoItem
            key="systemsScanned"
            className={
              'list-view-info-item-icon-count ' +
              (item.systems_scanned === 0 ? 'invisible' : '')
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
              {item.systems_scanned}
            </ListView.Expand>
          </ListView.InfoItem>,
          <ListView.InfoItem
            key="systemsFailed"
            className={
              'list-view-info-item-icon-count ' +
              (item.systems_failed === 0 ? 'invisible' : '')
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
              {item.systems_failed}
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
              expanded={expanded && expandType === 'scansCount'}
              toggleExpanded={() => {
                this.toggleExpand('scansCount');
              }}
            >
              {item.scans_count} {item.scans_count === 1 ? ' Scan' : ' Scans'}
            </ListView.Expand>
          </ListView.InfoItem>
        ]}
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
  onStart: PropTypes.func
};

export { ScanListItem };
