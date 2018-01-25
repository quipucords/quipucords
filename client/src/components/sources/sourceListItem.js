import React from 'react';
import PropTypes from 'prop-types';
import JSONPretty from 'react-json-pretty';
import {
  ListView,
  DropdownKebab,
  Button,
  MenuItem,
  Checkbox,
  Icon
} from 'patternfly-react';
import { bindMethods } from '../../common/helpers';

class SourceListItem extends React.Component {
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
    const { item, onItemSelectChange } = this.props;
    const { expanded, expandType } = this.state;

    let credentialCount = item.credentials ? item.credentials.length : 0;
    let okHostCount = item.hosts ? item.hosts.length : 0;
    let failedHostCount = item.failed_hosts ? item.hosts.length : 0;

    let itemIcon;
    switch (item.source_type) {
      case 'vcenter':
        itemIcon = <ListView.Icon type="pf" name="virtual-machine" />;
        break;
      case 'network':
        itemIcon = <ListView.Icon type="pf" name="network" />;
        break;
      case 'satellite':
        itemIcon = <ListView.Icon type="fa" name="space-shuttle" />;
        break;
      default:
        itemIcon = null;
    }

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
        actions={
          <span>
            <Button className="unavailable" bsStyle="default" key="scanButton">
              {'Scan'}
            </Button>
            <DropdownKebab
              id={'dropdownActions_' + item.id}
              key="kebab"
              pullRight
            >
              <MenuItem className="unavailable">Edit</MenuItem>
              <MenuItem className="unavailable">Search</MenuItem>
              <MenuItem className="unavailable">Duplicate</MenuItem>
              <MenuItem className="unavailable">Remove</MenuItem>
            </DropdownKebab>
          </span>
        }
        leftContent={itemIcon}
        heading={item.name}
        additionalInfo={[
          <ListView.InfoItem
            key="credentials"
            className="list-view-info-item-text-count"
          >
            <ListView.Expand
              expanded={expanded && expandType === 'credentials'}
              toggleExpanded={() => {
                this.toggleExpand('credentials');
              }}
            >
              {credentialCount}{' '}
              {credentialCount === 1 ? ' Credential' : ' Credentials'}
            </ListView.Expand>
          </ListView.InfoItem>,
          <ListView.InfoItem
            key="okHosts"
            className={
              'list-view-info-item-icon-count ' +
              (okHostCount === 0 ? 'invisible' : '')
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
              {okHostCount}
            </ListView.Expand>
          </ListView.InfoItem>,
          <ListView.InfoItem
            key="failedHosts"
            className={
              'list-view-info-item-icon-count ' +
              (failedHostCount === 0 ? 'invisible' : '')
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
              {failedHostCount}
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

SourceListItem.propTypes = {
  item: PropTypes.object,
  onItemSelectChange: PropTypes.func
};

export { SourceListItem };
