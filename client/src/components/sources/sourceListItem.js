import React from 'react';
import PropTypes from 'prop-types';
import JSONPretty from 'react-json-pretty';
import {
  ListView,
  DropdownKebab,
  Button,
  MenuItem,
  Checkbox
} from 'patternfly-react';

export const SourceListItem = ({ item }) => {
  let hostCount = item.hosts ? item.hosts.length : 0;

  let itemIcon;
  switch (item.source_type) {
    case 'vcenter':
      itemIcon = <ListView.Icon type="pf" name="virtual-machine" />;
      break;
    case 'network':
      itemIcon = <ListView.Icon type="pf" name="network" />;
      break;
    default:
      itemIcon = null;
  }

  return (
    <ListView.Item
      stacked
      key={item.id}
      checkboxInput={<Checkbox value={item.selected} bsClass="" />}
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
        <ListView.InfoItem key="hosts">
          <span className="pficon pficon-screen" />
          {hostCount} {hostCount === 1 ? ' Source' : ' Sources'}
        </ListView.InfoItem>
      ]}
    >
      <JSONPretty json={item} />
    </ListView.Item>
  );
};

SourceListItem.propTypes = {
  item: PropTypes.object
};
