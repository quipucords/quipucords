import React from 'react';
import PropTypes from 'prop-types';
import JSONPretty from 'react-json-pretty';
import {
  Button,
  Checkbox,
  DropdownKebab,
  ListView,
  MenuItem
} from 'patternfly-react';

export const ScanListItem = ({ item }) => {
  let sourcesCount = item.sources ? item.sources.length : 0;

  let statusName = '';
  let actionButtonLabel;
  let actionButtonType = 'primary';
  switch (item.status) {
    case 'completed':
      statusName = 'ok';
      actionButtonLabel = 'Download';
      break;
    case 'failed':
      statusName = 'error-circle-o';
      actionButtonLabel = 'Restart';
      break;
    case 'canceled':
      statusName = 'error-circle-o';
      actionButtonLabel = 'Restart Scan';
      break;
    case 'created':
      statusName = 'add-circle-o';
      actionButtonLabel = 'Cancel Scan';
      actionButtonType = 'danger';
      break;
    case 'running':
      statusName = 'on-running';
      actionButtonLabel = 'Cancel Scan';
      actionButtonType = 'danger';
      break;
    case 'paused':
      statusName = 'paused';
      actionButtonLabel = 'Continue';
      break;
    case 'pending':
      statusName = 'pending';
      actionButtonLabel = 'Cancel Scan';
      actionButtonType = 'danger';
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
      checkboxInput={<Checkbox value={item.selected} bsClass="" />}
      actions={
        <span>
          <Button
            className="unavailable"
            bsStyle={actionButtonType}
            key="authButton"
          >
            {actionButtonLabel}
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
      leftContent={leftContent}
      heading={'ID: ' + item.id}
      additionalInfo={[
        <ListView.InfoItem key="hosts">
          {sourcesCount} {sourcesCount === 1 ? ' Source' : ' Sources'}
        </ListView.InfoItem>
      ]}
    >
      <JSONPretty json={item} />
    </ListView.Item>
  );
};

ScanListItem.propTypes = {
  item: PropTypes.object
};
