import React from 'react';
import PropTypes from 'prop-types';
import cx from 'classnames';
import { connect } from 'react-redux';
import { Popover, OverlayTrigger, ListView, Button, Checkbox, Icon } from 'patternfly-react';
import _ from 'lodash';
import * as moment from 'moment';
import { helpers } from '../../common/helpers';
import Store from '../../redux/store';
import { viewTypes } from '../../redux/constants';
import { getScanResults } from '../../redux/actions/scansActions';
import SourceCredentialsList from './sourceCredentialsList';
import SourceHostList from './sourceHostList';
import SimpleTooltip from '../simpleTooltIp/simpleTooltip';
import ListStatusItem from '../listStatusItem/listStatusItem';

class SourceListItem extends React.Component {
  constructor() {
    super();

    helpers.bindMethods(this, ['itemSelectChange', 'toggleExpand', 'closeExpand']);

    this.state = {
      scanResultsPending: false,
      scanResultsError: null,
      scanResults: null
    };
  }

  componentWillReceiveProps(nextProps) {
    // Check for changes resulting in a fetch
    if (!_.isEqual(nextProps.lastRefresh, this.props.lastRefresh)) {
      this.loadExpandData(this.expandType());
    }
  }

  expandType() {
    const { item, expandedSources } = this.props;

    return _.get(
      _.find(expandedSources, nextExpanded => {
        return nextExpanded.id === item.id;
      }),
      'expandType'
    );
  }

  isSelected(item, selectedSources) {
    return (
      _.find(selectedSources, nextSelected => {
        return nextSelected.id === item.id;
      }) !== undefined
    );
  }

  itemSelectChange() {
    const { item, selectedSources } = this.props;

    Store.dispatch({
      type: this.isSelected(item, selectedSources) ? viewTypes.DESELECT_ITEM : viewTypes.SELECT_ITEM,
      viewType: viewTypes.SOURCES_VIEW,
      item: item
    });
  }

  loadExpandData(expandType) {
    const { item } = this.props;

    if (expandType === 'okHosts' || expandType === 'failedHosts') {
      this.setState({
        scanResultsPending: true,
        scanResultsError: null
      });
      this.props
        .getScanResults(item.connection.id)
        .then(results => {
          this.setState({
            scanResultsPending: false,
            scanResults: _.get(results.value, 'data')
          });
        })
        .catch(error => {
          this.setState({
            scanResultsPending: false,
            scanResultsError: helpers.getErrorMessageFromResults(error.payload)
          });
        });
    }
  }

  toggleExpand(expandType) {
    const { item } = this.props;

    if (expandType === this.expandType()) {
      Store.dispatch({
        type: viewTypes.EXPAND_ITEM,
        viewType: viewTypes.SOURCES_VIEW,
        item: item
      });
    } else {
      Store.dispatch({
        type: viewTypes.EXPAND_ITEM,
        viewType: viewTypes.SOURCES_VIEW,
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
      viewType: viewTypes.SOURCES_VIEW,
      item: item
    });
  }

  renderSourceType() {
    const { item } = this.props;
    const typeIcon = helpers.sourceTypeIcon(item.source_type);

    return (
      <SimpleTooltip id="sourceTypeTip" tooltip={helpers.sourceTypeString(item.source_type)}>
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
            <Icon type="pf" name="edit" aria-label="Edit" />
          </Button>
        </SimpleTooltip>
        <SimpleTooltip id="deleteTip" tooltip="Delete">
          <Button onClick={() => onDelete(item)} bsStyle="link" key="removeButton">
            <Icon type="pf" name="delete" aria-label="Delete" />
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

    const expandType = this.expandType();
    const credentialCount = _.size(_.get(item, 'credentials', []));
    let okHostCount = _.get(item, 'connection.systems_scanned', 0);
    let failedHostCount = _.get(item, 'connection.systems_failed', 0);

    if (helpers.DEV_MODE) {
      okHostCount = helpers.normalizeCount(okHostCount);
      failedHostCount = helpers.normalizeCount(failedHostCount);
    }

    return [
      <ListStatusItem
        key="credential"
        id="credential"
        count={credentialCount}
        emptyText="0 Credentials"
        tipSingular="Credential"
        tipPlural="Credentials"
        expanded={expandType === 'credentials'}
        expandType="credentials"
        toggleExpand={this.toggleExpand}
        iconType="fa"
        iconName="id-card"
      />,
      <ListStatusItem
        key="okHosts"
        id="okHosts"
        count={okHostCount}
        emptyText="0 Successful"
        tipSingular="Successful Authentication"
        tipPlural="Successful Authentications"
        expanded={expandType === 'okHosts'}
        expandType="okHosts"
        toggleExpand={this.toggleExpand}
        iconType="pf"
        iconName="ok"
      />,
      <ListStatusItem
        key="failedHosts"
        id="failedHosts"
        count={failedHostCount}
        emptyText="0 Failed"
        tipSingular="Failed Authentication"
        tipPlural="Failed Authentications"
        expanded={expandType === 'failedHosts'}
        expandType="failedHosts"
        toggleExpand={this.toggleExpand}
        iconType="pf"
        iconName="error-circle-o"
      />
    ];
  }

  renderExpansionContents() {
    const { item } = this.props;
    const { scanResults, scanResultsError, scanResultsPending } = this.state;

    switch (this.expandType()) {
      case 'okHosts':
        return (
          <SourceHostList
            scanResults={scanResults}
            scanResultsError={scanResultsError}
            scanResultsPending={scanResultsPending}
            status="success"
          />
        );
      case 'failedHosts':
        return (
          <SourceHostList
            scan={item}
            scanResults={scanResults}
            scanResultsError={scanResultsError}
            scanResultsPending={scanResultsPending}
            status="failed"
          />
        );
      case 'credentials':
        return <SourceCredentialsList source={item} />;
      default:
        return null;
    }
  }

  renderDescription() {
    const { item } = this.props;

    const itemHostsPopover = (
      <Popover id={helpers.generateId()} className="quipucords-sources-popover-scroll">
        <ul className="quipucords-popover-list">
          {item.hosts &&
            item.hosts.map((host, index) => {
              return <li key={index}>{host}</li>;
            })}
        </ul>
      </Popover>
    );

    let itemDescription;

    if (_.size(item.hosts)) {
      if (item.source_type === 'network') {
        itemDescription = (
          <ListView.DescriptionText>
            <OverlayTrigger trigger="click" rootClose placement="left" overlay={itemHostsPopover}>
              <Button bsStyle="link" className="quipucords-sources-network-button">
                Network Range
              </Button>
            </OverlayTrigger>
          </ListView.DescriptionText>
        );
      } else {
        itemDescription = <ListView.DescriptionText>{item.hosts[0]}</ListView.DescriptionText>;
      }
    }

    return (
      <div className="quipucords-split-description">
        <span className="quipucords-description-left">
          <ListView.DescriptionHeading>{item.name}</ListView.DescriptionHeading>
          {itemDescription}
        </span>
        <span className="quipucords-description-right">{this.renderScanStatus()}</span>
      </div>
    );
  }

  renderScanStatus() {
    const { item } = this.props;

    const scan = _.get(item, 'connection');
    let scanDescription = '';
    let scanTime = _.get(scan, 'end_time');
    let icon = null;

    switch (_.get(scan, 'status')) {
      case 'completed':
        scanDescription = 'Last Connected';
        icon = <Icon className="scan-status-icon" type="pf" name="ok" />;
        break;
      case 'failed':
        scanDescription = 'Connection Failed';
        icon = <Icon className="scan-status-icon" type="pf" name="error-circle-o" />;
        break;
      case 'canceled':
        scanDescription = 'Connection Canceled';
        icon = <Icon className="scan-status-icon" type="pf" name="error-circle-o" />;
        break;
      case 'created':
      case 'pending':
      case 'running':
        scanTime = _.get(scan, 'start_time');
        scanDescription = 'Connection in Progress';
        icon = <Icon className="scan-status-icon fa-spin" type="fa" name="spinner" />;
        break;
      case 'paused':
        scanDescription = 'Connection Paused';
        icon = <Icon className="scan-status-icon" type="pf" name="warning-triangle-o" />;
        break;
      default:
        return null;
    }

    return (
      <div className="scan-description">
        {icon}
        <div className="scan-status-text">
          <div>{scanDescription}</div>
          <div>
            {moment
              .utc(scanTime)
              .utcOffset(moment().utcOffset())
              .fromNow()}
          </div>
        </div>
      </div>
    );
  }
  render() {
    const { item, selectedSources } = this.props;
    const selected = this.isSelected(item, selectedSources);

    const classes = cx({
      'list-view-pf-top-align': true,
      active: selected
    });

    return (
      <ListView.Item
        key={item.id}
        stacked
        className={classes}
        checkboxInput={<Checkbox checked={selected} bsClass="" onChange={this.itemSelectChange} />}
        actions={this.renderActions()}
        leftContent={this.renderSourceType()}
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

SourceListItem.propTypes = {
  item: PropTypes.object,
  lastRefresh: PropTypes.number,
  onEdit: PropTypes.func,
  onDelete: PropTypes.func,
  onScan: PropTypes.func,
  getScanResults: PropTypes.func,
  selectedSources: PropTypes.array,
  expandedSources: PropTypes.array
};

const mapStateToProps = function(state) {
  return Object.assign({
    selectedSources: state.viewOptions[viewTypes.SOURCES_VIEW].selectedItems,
    expandedSources: state.viewOptions[viewTypes.SOURCES_VIEW].expandedItems
  });
};

const mapDispatchToProps = (dispatch, ownProps) => ({
  getScanResults: id => dispatch(getScanResults(id))
});

export default connect(mapStateToProps, mapDispatchToProps)(SourceListItem);
