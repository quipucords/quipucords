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
    const { expanded, expandType } = this.state;

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
            expanded={expanded && expandType === 'credentials'}
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
            (okHostCount === 1 ? ' Successful System' : ' Successful Systems')
          }
        >
          <ListView.Expand
            expanded={expanded && expandType === 'okHosts'}
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
            (failedHostCount === 1 ? ' Failed System' : ' Failed Systems')
          }
        >
          <ListView.Expand
            expanded={expanded && expandType === 'failedHosts'}
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
    const { expandType } = this.state;

    switch (expandType) {
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

  render() {
    const { item, onItemSelectChange } = this.props;
    const { expanded } = this.state;

    return (
      <ListView.Item
        key={item.id}
        checkboxInput={
          <Checkbox
            checked={item.selected}
            bsClass=""
            onClick={e => onItemSelectChange(item)}
          />
        }
        actions={this.renderActions()}
        leftContent={this.renderSourceType()}
        heading={item.name}
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

SourceListItem.propTypes = {
  item: PropTypes.object,
  onItemSelectChange: PropTypes.func,
  onEdit: PropTypes.func,
  onDelete: PropTypes.func,
  onScan: PropTypes.func
};

export { SourceListItem };
