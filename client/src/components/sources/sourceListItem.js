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

export const SourceListItem = ({ item, onItemSelectChange }) => {
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
          <Button className="unavailable" bsStyle="default" key="authButton">
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
          {credentialCount}{' '}
          {credentialCount === 1 ? ' Credential' : ' Credentials'}
        </ListView.InfoItem>,
        <ListView.InfoItem
          key="okHosts"
          className={
            'list-view-info-item-icon-count ' +
            (okHostCount === 0 ? 'invisible' : '')
          }
        >
          <Icon type="pf" name="ok" />
          {okHostCount}
        </ListView.InfoItem>,
        <ListView.InfoItem
          key="failedHosts"
          className={
            'list-view-info-item-icon-count ' +
            (failedHostCount === 0 ? 'invisible' : '')
          }
        >
          <Icon type="pf" name="error-circle-o" />
          {failedHostCount}
        </ListView.InfoItem>
      ]}
    >
      <JSONPretty json={item} />
    </ListView.Item>
  );
};

SourceListItem.propTypes = {
  item: PropTypes.object,
  onItemSelectChange: PropTypes.func
};
