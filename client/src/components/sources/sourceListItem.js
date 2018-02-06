import React from 'react';
import PropTypes from 'prop-types';
import JSONPretty from 'react-json-pretty';
import { ListView, Button, Checkbox, Icon } from 'patternfly-react';
import { helpers } from '../../common/helpers';
import { SourceCredentialsList } from './sourceCredentialsList';
import { SourceHostsList } from './sourceHostList';
import { SimpleTooltip } from '../simpleTooltIp/simpleTooltip';

class SourceListItem extends React.Component {
  constructor() {
    super();

    helpers.bindMethods(this, ['toggleExpand', 'closeExpand']);
  }

  toggleExpand(expandType) {
    const { item } = this.props;
    item.expanded = !item.expanded;
    item.expandType = expandType;
    this.forceUpdate();
  }

  closeExpand() {
    const { item } = this.props;
    item.expanded = false;
    this.forceUpdate();
  }

  renderSourceType() {
    const { item } = this.props;

    let typeIcon = helpers.sourceTypeIcon(item.source_type);

    return (
      <SimpleTooltip
        id="sourceTypeTip"
        tooltip={helpers.sourceTypeString(item.source_type)}
      >
        <ListView.Icon type={typeIcon.type} name={typeIcon.name} />
      </SimpleTooltip>
    );
  }

  renderActions() {
    const { item, onEdit, onDelete, onScan } = this.props;

    return (
      <span>
        <SimpleTooltip id="editTip" tooltip="Edit">
          <Button onClick={() => onEdit(item)} bsStyle="link" key="editButton">
            <Icon type="pf" name="edit" atria-label="Edit" />
          </Button>
        </SimpleTooltip>
        <SimpleTooltip id="deleteTip" tooltip="Delete">
          <Button
            onClick={() => onDelete(item)}
            bsStyle="link"
            key="removeButton"
          >
            <Icon type="pf" name="delete" atria-label="Delete" />
          </Button>
        </SimpleTooltip>
        <Button onClick={() => onScan(item)} key="scanButton">
          Scan
        </Button>
      </span>
    );
  }

  renderStatusItems() {
    const { item } = this.props;

    let credentialCount = item.credentials ? item.credentials.length : 0;
    let okHostCount = item.hosts ? item.hosts.length : 0;
    let failedHostCount = item.failed_hosts ? item.failed_hosts.length : 0;

    return [
      <ListView.InfoItem
        key="credentials"
        className={
          'list-view-info-item-icon-count ' +
          (credentialCount === 0 ? 'invisible' : '')
        }
      >
        <SimpleTooltip
          id="credentialsTip"
          tooltip={
            credentialCount +
            (credentialCount === 1 ? ' Credential' : ' Credentials')
          }
        >
          <ListView.Expand
            expanded={item.expanded && item.expandType === 'credentials'}
            toggleExpanded={() => {
              this.toggleExpand('credentials');
            }}
          >
            <Icon
              className="list-view-compound-item-icon"
              type="fa"
              name="key"
            />
            <strong>{credentialCount}</strong>
          </ListView.Expand>
        </SimpleTooltip>
      </ListView.InfoItem>,
      <ListView.InfoItem
        key="okHosts"
        className={
          'list-view-info-item-icon-count ' +
          (okHostCount === 0 ? 'invisible' : '')
        }
      >
        <SimpleTooltip
          id="okHostsTip"
          tooltip={
            okHostCount +
            (okHostCount === 1
              ? ' Successful Authentication'
              : ' Successful Authentications')
          }
        >
          <ListView.Expand
            expanded={item.expanded && item.expandType === 'okHosts'}
            toggleExpanded={() => {
              this.toggleExpand('okHosts');
            }}
          >
            <Icon
              className="list-view-compound-item-icon"
              type="pf"
              name="ok"
            />
            <strong>{okHostCount}</strong>
          </ListView.Expand>
        </SimpleTooltip>
      </ListView.InfoItem>,
      <ListView.InfoItem
        key="failedHosts"
        className={
          'list-view-info-item-icon-count ' +
          (failedHostCount === 0 ? 'invisible' : '')
        }
      >
        <SimpleTooltip
          id="failedHostsTip"
          tooltip={
            failedHostCount +
            (failedHostCount === 1
              ? ' Failed Authentication'
              : ' Failed Authentications')
          }
        >
          <ListView.Expand
            expanded={item.expanded && item.expandType === 'failedHosts'}
            toggleExpanded={() => {
              this.toggleExpand('failedHosts');
            }}
          >
            <Icon
              className="list-view-compound-item-icon"
              type="pf"
              name="error-circle-o"
            />
            <strong>{failedHostCount}</strong>
          </ListView.Expand>
        </SimpleTooltip>
      </ListView.InfoItem>
    ];
  }

  renderExpansionContents() {
    const { item } = this.props;

    switch (item.expandType) {
      case 'okHosts':
        return <SourceHostsList hosts={item.hosts} status="ok" />;
      case 'failedHosts':
        return (
          <SourceHostsList hosts={item.failed_hosts} status="error-circle-o" />
        );
      case 'credentials':
        return <SourceCredentialsList source={item} />;
      default:
        return <JSONPretty json={item} />;
    }
  }

  renderDescription() {
    const { item } = this.props;
    return (
      <div className="quipucords-split-description">
        <span className="quipucords-description-left">
          <ListView.DescriptionHeading>{item.name}</ListView.DescriptionHeading>
          {item.hosts &&
            item.hosts.map((host, index) => {
              return (
                <ListView.DescriptionText key={index}>
                  {host}
                </ListView.DescriptionText>
              );
            })}
        </span>
        <span className="quipucords-description-right">
          {this.renderScanStatus()}
        </span>
      </div>
    );
  }

  renderScanStatus() {
    const { item } = this.props;

    let scanDescription = '';
    let scan = item.connection_scan;
    if (!scan) {
      scan = {
        status: 'running'
      };
    }

    let icon = null;
    switch (scan.status) {
      case 'completed':
        scanDescription = 'Last Connected';
        icon = <Icon className="scan-status-icon" type="pf" name="ok" />;
        break;
      case 'failed':
        scanDescription = 'Connection Failed';
        icon = (
          <Icon className="scan-status-icon" type="pf" name="error-circle-o" />
        );
        break;
      case 'canceled':
        scanDescription = 'Connection Canceled';
        icon = (
          <Icon className="scan-status-icon" type="pf" name="error-circle-o" />
        );
        break;
      case 'created':
      case 'pending':
      case 'running':
        scanDescription = 'Connection in Progress';
        icon = (
          <Icon className="scan-status-icon fa-spin" type="fa" name="spinner" />
        );
        break;
      case 'paused':
        scanDescription = 'Connection Paused';
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
  render() {
    const { item, onItemSelectChange } = this.props;

    return (
      <ListView.Item
        key={item.id}
        stacked
        className="list-view-pf-top-align"
        checkboxInput={
          <Checkbox
            checked={item.selected}
            bsClass=""
            onClick={e => onItemSelectChange(item)}
          />
        }
        actions={this.renderActions()}
        leftContent={this.renderSourceType()}
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

SourceListItem.propTypes = {
  item: PropTypes.object,
  onItemSelectChange: PropTypes.func,
  onEdit: PropTypes.func,
  onDelete: PropTypes.func,
  onScan: PropTypes.func
};

export { SourceListItem };
